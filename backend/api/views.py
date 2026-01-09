import csv
import io
from datetime import datetime

from django.contrib.auth import authenticate
from decimal import Decimal

from django.http import HttpResponse
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Campaign, Child, ChildCampaignTarget, GuardianChildLink, Product, Sale, Team

from .serializers import (
	CampaignSerializer,
	ChildSerializer,
	ChildYearlyStatsSerializer,
	ProductSerializer,
	ResolvedChildCampaignTargetSerializer,
	ChildCampaignSummarySerializer,
	TeamYearlyStatsSerializer,
		TeamCampaignSummarySerializer,
		DeviceTokenRegisterSerializer,
	SaleCreateSerializer,
	SaleListItemSerializer,
	SaleSerializer,
	SaleUpdateSerializer,
	TeamSerializer,
)

from .models import DeviceToken


def _get_user_team(user):
	if getattr(user, 'team_id', None):
		return user.team
	if getattr(user, 'role', None) == 'coach':
		return Team.objects.filter(coach=user).first()
	return None


def _parse_year_param(request):
	year_raw = None
	if hasattr(request, 'query_params'):
		year_raw = request.query_params.get('year')
	if year_raw is None:
		year_raw = request.GET.get('year')
	if not year_raw:
		return None, Response({'detail': 'year query param is required'}, status=400)
	try:
		year = int(year_raw)
	except ValueError:
		return None, Response({'detail': 'year must be an integer'}, status=400)
	if year < 1970 or year > 2100:
		return None, Response({'detail': 'year out of supported range'}, status=400)
	return year, None


def _child_short_name(child_obj):
	name = child_obj.first_name
	if child_obj.last_initial:
		name = f'{name} {child_obj.last_initial}'
	return name


@api_view(['GET'])
def health(request):
	return Response({"status": "ok"})


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
	email = (request.data or {}).get('email')
	password = (request.data or {}).get('password')

	if not email or not password:
		return Response({'detail': 'email and password are required'}, status=400)

	user = authenticate(request, email=email, password=password)
	if user is None:
		return Response({'detail': 'Invalid credentials'}, status=401)
	if not user.is_active:
		return Response({'detail': 'User is inactive'}, status=403)

	refresh = RefreshToken.for_user(user)
	return Response(
		{
			'access_token': str(refresh.access_token),
			'user': {
				'id': str(user.id),
				'email': user.email,
				'role': user.role,
				'first_name': user.first_name,
				'last_name': user.last_name,
			},
		}
	)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
	user = request.user
	return Response(
		{
			'id': str(user.id),
			'email': user.email,
			'role': getattr(user, 'role', None),
			'first_name': user.first_name,
			'last_name': user.last_name,
			'children': [],
		}
	)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team(request):
	user = request.user

	if getattr(user, 'team_id', None):
		return Response(TeamSerializer(user.team).data)

	if getattr(user, 'role', None) == 'coach':
		team_obj = Team.objects.filter(coach=user).first()
		if team_obj:
			return Response(TeamSerializer(team_obj).data)

	return Response({'detail': 'No team associated with user'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
	serializer = DeviceTokenRegisterSerializer(data=request.data or {})
	serializer.is_valid(raise_exception=True)

	token = serializer.validated_data['token']
	platform = serializer.validated_data['platform']
	provider = serializer.validated_data.get('provider', DeviceToken.Provider.FCM)

	obj, created = DeviceToken.objects.update_or_create(
		token=token,
		defaults={
			'user': request.user,
			'platform': platform,
			'provider': provider,
			'is_active': True,
			'last_seen_at': timezone.now(),
		},
	)

	return Response(
		{
			'id': obj.id,
			'platform': obj.platform,
			'provider': obj.provider,
			'is_active': obj.is_active,
			'last_seen_at': obj.last_seen_at.isoformat(),
		},
		status=201 if created else 200,
	)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def campaigns(request):
	user = request.user

	if request.method == 'GET':
		team_obj = _get_user_team(user)
		if team_obj is None:
			return Response({'detail': 'No team associated with user'}, status=404)
		qs = Campaign.objects.filter(team=team_obj).order_by('-start_date', '-created_at')
		return Response(CampaignSerializer(qs, many=True).data)

	# POST
	if getattr(user, 'role', None) != 'coach':
		return Response({'detail': 'Only coaches can create campaigns'}, status=403)

	data = request.data or {}
	team_id = data.get('team_id') or data.get('team')
	if not team_id:
		return Response({'detail': 'team_id is required'}, status=400)

	allowed_teams = Team.objects.filter(coach=user)
	if getattr(user, 'team_id', None):
		allowed_teams = allowed_teams.filter(id=user.team_id)

	team_obj = allowed_teams.filter(id=team_id).first()
	if team_obj is None:
		return Response({'detail': 'Team not found'}, status=404)

	create_payload = {
		'team': str(team_obj.id),
		'name': data.get('name'),
		'description': data.get('description', ''),
		'start_date': data.get('start_date'),
		'end_date': data.get('end_date'),
		'default_target_units_per_child': data.get('default_target_units_per_child', 0),
		'buyout_amount_per_child': data.get('buyout_amount_per_child', 0),
		'currency': data.get('currency', 'SEK'),
		'is_active': data.get('is_active', True),
	}

	serializer = CampaignSerializer(data=create_payload)
	serializer.is_valid(raise_exception=True)
	campaign_obj = serializer.save()

	if campaign_obj.is_active:
		Campaign.objects.filter(team=team_obj).exclude(id=campaign_obj.id).update(is_active=False)

	return Response(CampaignSerializer(campaign_obj).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_campaign(request):
	team_obj = _get_user_team(request.user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = (
		Campaign.objects.filter(team=team_obj, is_active=True)
		.order_by('-start_date', '-created_at')
		.first()
	)
	if campaign_obj is None:
		return Response({'detail': 'No active campaign'}, status=404)

	return Response(CampaignSerializer(campaign_obj).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def children(request):
	user = request.user
	if getattr(user, 'role', None) != 'guardian':
		return Response({'detail': 'Only guardians can list children'}, status=403)

	child_ids = GuardianChildLink.objects.filter(guardian=user).values_list('child_id', flat=True)
	qs = (
		user.team.children.filter(id__in=child_ids, is_active=True)
		.select_related('team')
		.order_by('first_name', 'id')
	)
	return Response(ChildSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def child_campaign_target(request, campaign_id, child_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
	if campaign_obj is None:
		return Response({'detail': 'Campaign not found'}, status=404)

	child_obj = Child.objects.filter(id=child_id, team=team_obj).first()
	if child_obj is None:
		return Response({'detail': 'Child not found'}, status=404)

	role = getattr(user, 'role', None)
	if role == 'guardian':
		if not GuardianChildLink.objects.filter(guardian=user, child=child_obj).exists():
			return Response({'detail': 'Child not found'}, status=404)
	elif role != 'coach':
		return Response({'detail': 'Forbidden'}, status=403)

	link_obj = ChildCampaignTarget.objects.filter(child=child_obj, campaign=campaign_obj).first()

	resolved_target_units = (
		link_obj.target_units
		if link_obj is not None and link_obj.target_units is not None
		else campaign_obj.default_target_units_per_child
	)
	resolved_buyout_amount = (
		link_obj.buyout_amount
		if link_obj is not None and link_obj.buyout_amount is not None
		else campaign_obj.buyout_amount_per_child
	)
	resolved_has_paid_buyout = link_obj.has_paid_buyout if link_obj is not None else False

	payload = {
		'child_id': child_obj.id,
		'campaign_id': campaign_obj.id,
		'target_units': resolved_target_units,
		'buyout_amount': resolved_buyout_amount,
		'has_paid_buyout': resolved_has_paid_buyout,
		'resolved_from': 'child' if link_obj is not None else 'campaign',
	}
	return Response(ResolvedChildCampaignTargetSerializer(payload).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def campaign_products(request, campaign_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
	if campaign_obj is None:
		return Response({'detail': 'Campaign not found'}, status=404)

	if request.method == 'GET':
		qs = Product.objects.filter(campaign=campaign_obj, is_active=True).order_by('name', 'id')
		return Response(ProductSerializer(qs, many=True).data)

	# POST
	if getattr(user, 'role', None) != 'coach':
		return Response({'detail': 'Only coaches can create products'}, status=403)

	if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
		return Response({'detail': 'Forbidden'}, status=403)

	data = request.data or {}
	payload = {
		'campaign': str(campaign_obj.id),
		'name': data.get('name'),
		'description': data.get('description', ''),
		'unit_price': data.get('unit_price'),
		'profit_per_unit': data.get('profit_per_unit'),
		'is_active': data.get('is_active', True),
	}
	serializer = ProductSerializer(data=payload)
	serializer.is_valid(raise_exception=True)
	product_obj = serializer.save()
	return Response(ProductSerializer(product_obj).data, status=201)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def product_detail(request, product_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	product_obj = (
		Product.objects.select_related('campaign', 'campaign__team')
		.filter(id=product_id, campaign__team=team_obj)
		.first()
	)
	if product_obj is None:
		return Response({'detail': 'Product not found'}, status=404)

	if getattr(user, 'role', None) != 'coach':
		return Response({'detail': 'Only coaches can update products'}, status=403)
	if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
		return Response({'detail': 'Forbidden'}, status=403)

	serializer = ProductSerializer(product_obj, data=request.data or {}, partial=True)
	serializer.is_valid(raise_exception=True)
	serializer.save()
	return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def campaign_sales(request, campaign_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
	if campaign_obj is None:
		return Response({'detail': 'Campaign not found'}, status=404)

	input_serializer = SaleCreateSerializer(data=request.data or {})
	input_serializer.is_valid(raise_exception=True)
	data = input_serializer.validated_data

	quantity = data['quantity']
	if quantity <= 0:
		return Response({'detail': 'quantity must be > 0'}, status=400)

	child_obj = Child.objects.filter(id=data['child_id'], team=team_obj, is_active=True).first()
	if child_obj is None:
		return Response({'detail': 'Child not found'}, status=404)

	role = getattr(user, 'role', None)
	if role == 'guardian':
		if not GuardianChildLink.objects.filter(guardian=user, child=child_obj).exists():
			return Response({'detail': 'Child not found'}, status=404)
	elif role == 'coach':
		if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
			return Response({'detail': 'Forbidden'}, status=403)
	else:
		return Response({'detail': 'Forbidden'}, status=403)

	product_obj = Product.objects.filter(id=data['product_id'], campaign=campaign_obj, is_active=True).first()
	if product_obj is None:
		return Response({'detail': 'Product not found'}, status=404)

	sale_obj = Sale.objects.create(
		campaign=campaign_obj,
		child=child_obj,
		product=product_obj,
		quantity=quantity,
		buyer_name=data.get('buyer_name', ''),
		is_paid=data.get('is_paid', False),
		is_delivered=data.get('is_delivered', False),
		recorded_by=user,
	)
	return Response(SaleSerializer(sale_obj).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_sales_my_children(request, campaign_id):
	user = request.user
	if getattr(user, 'role', None) != 'guardian':
		return Response({'detail': 'Only guardians can list sales'}, status=403)

	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
	if campaign_obj is None:
		return Response({'detail': 'Campaign not found'}, status=404)

	child_ids = set(
		GuardianChildLink.objects.filter(guardian=user)
		.values_list('child_id', flat=True)
	)

	child_id_filter = request.query_params.get('child_id')
	if child_id_filter:
		if child_id_filter not in {str(cid) for cid in child_ids}:
			return Response({'detail': 'Child not found'}, status=404)
		child_ids = {child_id_filter}

	try:
		offset = int(request.query_params.get('offset', 0))
		limit = int(request.query_params.get('limit', 100))
	except (TypeError, ValueError):
		return Response({'detail': 'offset and limit must be integers'}, status=400)

	if offset < 0 or limit < 1:
		return Response({'detail': 'offset must be >= 0 and limit must be >= 1'}, status=400)
	if limit > 500:
		limit = 500

	qs = (
		Sale.objects.filter(campaign=campaign_obj, child_id__in=child_ids)
		.select_related('product', 'child')
		.order_by('-recorded_at', '-created_at')
	)

	items = list(qs[offset : offset + limit])
	return Response(SaleListItemSerializer(items, many=True).data)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def sale_detail(request, sale_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	sale_obj = (
		Sale.objects.select_related('campaign', 'campaign__team', 'product')
		.filter(id=sale_id, campaign__team=team_obj)
		.first()
	)
	if sale_obj is None:
		return Response({'detail': 'Sale not found'}, status=404)

	role = getattr(user, 'role', None)
	if role == 'guardian':
		if sale_obj.recorded_by_id != user.id:
			return Response({'detail': 'Sale not found'}, status=404)
	elif role == 'coach':
		if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
			return Response({'detail': 'Forbidden'}, status=403)
	else:
		return Response({'detail': 'Forbidden'}, status=403)

	if request.method == 'DELETE':
		sale_obj.delete()
		return Response(status=204)

	# PATCH
	input_serializer = SaleUpdateSerializer(data=request.data or {})
	input_serializer.is_valid(raise_exception=True)
	data = input_serializer.validated_data

	if 'quantity' in data:
		if data['quantity'] <= 0:
			return Response({'detail': 'quantity must be > 0'}, status=400)
		sale_obj.quantity = data['quantity']
	if 'is_paid' in data:
		sale_obj.is_paid = data['is_paid']
	if 'is_delivered' in data:
		sale_obj.is_delivered = data['is_delivered']

	sale_obj.save()
	return Response(SaleSerializer(sale_obj).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def child_campaign_summary(request, child_id, campaign_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
	if campaign_obj is None:
		return Response({'detail': 'Campaign not found'}, status=404)

	child_obj = Child.objects.filter(id=child_id, team=team_obj).first()
	if child_obj is None:
		return Response({'detail': 'Child not found'}, status=404)

	role = getattr(user, 'role', None)
	if role == 'guardian':
		if not GuardianChildLink.objects.filter(guardian=user, child=child_obj).exists():
			return Response({'detail': 'Child not found'}, status=404)
	elif role == 'coach':
		if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
			return Response({'detail': 'Forbidden'}, status=403)
	else:
		return Response({'detail': 'Forbidden'}, status=403)

	target_obj = ChildCampaignTarget.objects.filter(child=child_obj, campaign=campaign_obj).first()
	target_units = (
		target_obj.target_units
		if target_obj is not None and target_obj.target_units is not None
		else campaign_obj.default_target_units_per_child
	)

	agg = Sale.objects.filter(campaign=campaign_obj, child=child_obj).aggregate(
		units=Coalesce(Sum('quantity'), 0),
		amount=Coalesce(Sum('total_price'), Decimal('0.00')),
	)
	total_units_sold = int(agg['units'] or 0)
	total_sales_amount = agg['amount'] or Decimal('0.00')

	remaining_units_to_target = max(int(target_units) - total_units_sold, 0)
	if int(target_units) <= 0:
		progress_percent = Decimal('0.00')
	else:
		progress_percent = (Decimal(total_units_sold) / Decimal(int(target_units)) * Decimal('100.0'))
		if progress_percent > Decimal('100.0'):
			progress_percent = Decimal('100.0')
		progress_percent = progress_percent.quantize(Decimal('0.01'))

	payload = {
		'child_id': child_obj.id,
		'campaign_id': campaign_obj.id,
		'target_units': int(target_units),
		'total_units_sold': total_units_sold,
		'total_sales_amount': total_sales_amount,
		'remaining_units_to_target': remaining_units_to_target,
		'progress_percent': progress_percent,
	}
	return Response(ChildCampaignSummarySerializer(payload).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_campaign_summary(request, campaign_id):
		user = request.user
		team_obj = _get_user_team(user)
		if team_obj is None:
				return Response({'detail': 'No team associated with user'}, status=404)

		campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
		if campaign_obj is None:
				return Response({'detail': 'Campaign not found'}, status=404)

		role = getattr(user, 'role', None)
		if role == 'coach':
				if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
						return Response({'detail': 'Forbidden'}, status=403)
		elif role != 'guardian':
				return Response({'detail': 'Forbidden'}, status=403)

		children_qs = (
				Child.objects.filter(team=team_obj, is_active=True)
				.order_by('first_name', 'id')
		)
		child_ids = list(children_qs.values_list('id', flat=True))

		targets = ChildCampaignTarget.objects.filter(
				campaign=campaign_obj,
				child_id__in=child_ids,
		).values('child_id', 'target_units')
		target_by_child_id = {row['child_id']: row['target_units'] for row in targets}

		sales_units = (
				Sale.objects.filter(campaign=campaign_obj, child_id__in=child_ids)
				.values('child_id')
				.annotate(units=Coalesce(Sum('quantity'), 0))
		)
		units_by_child_id = {row['child_id']: int(row['units'] or 0) for row in sales_units}

		children_payload = []
		team_total_units_sold = 0
		team_target_units = 0
		for child_obj in children_qs:
				target_units = target_by_child_id.get(child_obj.id)
				if target_units is None:
					target_units = campaign_obj.default_target_units_per_child
				target_units = int(target_units)
				total_units_sold = int(units_by_child_id.get(child_obj.id, 0))

				if target_units <= 0:
						progress_percent = Decimal('0.00')
				else:
						progress_percent = (
								Decimal(total_units_sold) / Decimal(target_units) * Decimal('100.0')
						)
						if progress_percent > Decimal('100.0'):
								progress_percent = Decimal('100.0')
						progress_percent = progress_percent.quantize(Decimal('0.01'))

				name = child_obj.first_name
				if child_obj.last_initial:
						name = f'{name} {child_obj.last_initial}'

				children_payload.append(
						{
								'id': child_obj.id,
								'name': name,
								'target_units': target_units,
								'total_units_sold': total_units_sold,
								'progress_percent': progress_percent,
						}
				)

				team_total_units_sold += total_units_sold
				team_target_units += target_units

		if team_target_units <= 0:
				team_progress_percent = Decimal('0.00')
		else:
				team_progress_percent = (
						Decimal(team_total_units_sold) / Decimal(team_target_units) * Decimal('100.0')
				)
				if team_progress_percent > Decimal('100.0'):
						team_progress_percent = Decimal('100.0')
				team_progress_percent = team_progress_percent.quantize(Decimal('0.01'))

		payload = {
				'campaign': {'id': campaign_obj.id, 'name': campaign_obj.name},
				'team': {'id': team_obj.id, 'name': team_obj.name},
				'children': children_payload,
				'team_total_units_sold': team_total_units_sold,
				'team_target_units': team_target_units,
				'team_progress_percent': team_progress_percent,
		}
		return Response(TeamCampaignSummarySerializer(payload).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_team_year(request):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	if getattr(user, 'role', None) != 'coach':
		return Response({'detail': 'Forbidden'}, status=403)
	if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
		return Response({'detail': 'Forbidden'}, status=403)

	year, err = _parse_year_param(request)
	if err is not None:
		return err

	sales_qs = Sale.objects.filter(child__team=team_obj, recorded_at__year=year)

	totals = sales_qs.aggregate(
		units=Coalesce(Sum('quantity'), 0),
		amount=Coalesce(Sum('total_price'), Decimal('0.00')),
	)
	total_units_sold = int(totals['units'] or 0)
	total_sales_amount = totals['amount'] or Decimal('0.00')

	rows = (
		sales_qs.values(
			'child_id',
			'child__first_name',
			'child__last_initial',
			'campaign_id',
			'campaign__name',
		)
		.annotate(
			units=Coalesce(Sum('quantity'), 0),
			amount=Coalesce(Sum('total_price'), Decimal('0.00')),
		)
		.order_by('child__first_name', 'child_id', 'campaign__name', 'campaign_id')
	)

	children_by_id = {}
	for row in rows:
		child_id = row['child_id']
		child_name = row['child__first_name']
		if row.get('child__last_initial'):
			child_name = f"{child_name} {row['child__last_initial']}"

		entry = children_by_id.get(child_id)
		if entry is None:
			entry = {
				'child_id': child_id,
				'name': child_name,
				'total_units_sold': 0,
				'total_sales_amount': Decimal('0.00'),
				'campaigns': [],
			}
			children_by_id[child_id] = entry

		units_sold = int(row['units'] or 0)
		sales_amount = row['amount'] or Decimal('0.00')
		entry['total_units_sold'] += units_sold
		entry['total_sales_amount'] += sales_amount
		entry['campaigns'].append(
			{
				'campaign_id': row['campaign_id'],
				'campaign_name': row['campaign__name'],
				'units_sold': units_sold,
				'sales_amount': sales_amount,
			}
		)

	children_payload = list(children_by_id.values())

	payload = {
		'team': {'id': team_obj.id, 'name': team_obj.name},
		'year': year,
		'total_units_sold': total_units_sold,
		'total_sales_amount': total_sales_amount,
		'children': children_payload,
	}
	return Response(TeamYearlyStatsSerializer(payload).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_child_year(request, child_id):
	user = request.user
	team_obj = _get_user_team(user)
	if team_obj is None:
		return Response({'detail': 'No team associated with user'}, status=404)

	child_obj = Child.objects.filter(id=child_id, team=team_obj).first()
	if child_obj is None:
		return Response({'detail': 'Child not found'}, status=404)

	role = getattr(user, 'role', None)
	if role == 'guardian':
		if not GuardianChildLink.objects.filter(guardian=user, child=child_obj).exists():
			return Response({'detail': 'Child not found'}, status=404)
	elif role == 'coach':
		if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
			return Response({'detail': 'Forbidden'}, status=403)
	else:
		return Response({'detail': 'Forbidden'}, status=403)

	year, err = _parse_year_param(request)
	if err is not None:
		return err

	sales_qs = Sale.objects.filter(child=child_obj, recorded_at__year=year)
	totals = sales_qs.aggregate(
		units=Coalesce(Sum('quantity'), 0),
		amount=Coalesce(Sum('total_price'), Decimal('0.00')),
	)
	total_units_sold = int(totals['units'] or 0)
	total_sales_amount = totals['amount'] or Decimal('0.00')

	rows = (
		sales_qs.values('campaign_id', 'campaign__name')
		.annotate(
			units=Coalesce(Sum('quantity'), 0),
			amount=Coalesce(Sum('total_price'), Decimal('0.00')),
		)
		.order_by('campaign__name', 'campaign_id')
	)
	campaigns_payload = [
		{
			'campaign_id': row['campaign_id'],
			'campaign_name': row['campaign__name'],
			'units_sold': int(row['units'] or 0),
			'sales_amount': row['amount'] or Decimal('0.00'),
		}
		for row in rows
	]

	payload = {
		'child': {'id': child_obj.id, 'name': _child_short_name(child_obj)},
		'year': year,
		'total_units_sold': total_units_sold,
		'total_sales_amount': total_sales_amount,
		'campaigns': campaigns_payload,
	}
	return Response(ChildYearlyStatsSerializer(payload).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def campaign_export_csv(request, campaign_id):
		user = request.user
		team_obj = _get_user_team(user)
		if team_obj is None:
				return Response({'detail': 'No team associated with user'}, status=404)

		campaign_obj = Campaign.objects.filter(id=campaign_id, team=team_obj).first()
		if campaign_obj is None:
				return Response({'detail': 'Campaign not found'}, status=404)

		if getattr(user, 'role', None) != 'coach':
				return Response({'detail': 'Only coaches can export CSV'}, status=403)
		if Team.objects.filter(id=team_obj.id, coach=user).exists() is False:
				return Response({'detail': 'Forbidden'}, status=403)

		qs = (
				Sale.objects.filter(campaign=campaign_obj)
				.select_related('child', 'product')
				.order_by('child__first_name', 'child__id', 'product__name', 'id')
		)

		buffer = io.StringIO()
		writer = csv.writer(buffer)
		writer.writerow(
				[
						'child_id',
						'child_name',
						'product_id',
						'product_name',
						'quantity',
						'buyer_name',
						'is_paid',
						'is_delivered',
						'total_price',
				]
		)

		for sale in qs:
				child_name = sale.child.first_name
				if sale.child.last_initial:
						child_name = f'{child_name} {sale.child.last_initial}'
				writer.writerow(
						[
								str(sale.child_id),
								child_name,
								str(sale.product_id),
								sale.product.name,
								sale.quantity,
								sale.buyer_name,
								str(bool(sale.is_paid)).lower(),
								str(bool(sale.is_delivered)).lower(),
								f'{sale.total_price:.2f}',
						]
				)

		response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
		response['Content-Disposition'] = f'attachment; filename="campaign-{campaign_obj.id}-sales.csv"'
		return response


