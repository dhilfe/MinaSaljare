from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Campaign, Team

from core.models import Child, ChildCampaignTarget, GuardianChildLink, Product, Sale


class CampaignApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()
		self.coach = User.objects.create_user(
			email='coach@example.com',
			password='pass',
			role='coach',
			first_name='Coach',
			last_name='One',
		)
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)

		self.guardian = User.objects.create_user(
			email='guardian@example.com',
			password='pass',
			role='guardian',
			team=self.team,
			first_name='Guardian',
			last_name='One',
		)

	def test_active_campaign_returns_404_when_missing(self):
		self.client.force_authenticate(user=self.guardian)
		res = self.client.get('/api/v1/campaigns/active/')
		self.assertEqual(res.status_code, 404)

	def test_coach_can_create_campaign(self):
		self.client.force_authenticate(user=self.coach)
		payload = {
			'team_id': str(self.team.id),
			'name': 'Salami Spring 2026',
			'description': 'Fundraiser',
			'start_date': '2026-03-01',
			'end_date': '2026-03-31',
			'default_target_units_per_child': 20,
			'buyout_amount_per_child': '1000.00',
			'currency': 'SEK',
			'is_active': True,
		}
		res = self.client.post('/api/v1/campaigns/', payload, format='json')
		self.assertEqual(res.status_code, 201)
		self.assertEqual(res.data['name'], 'Salami Spring 2026')
		self.assertEqual(str(res.data['team']), str(self.team.id))
		self.assertTrue(res.data['is_active'])
		self.assertEqual(Campaign.objects.filter(team=self.team).count(), 1)

	def test_guardian_cannot_create_campaign(self):
		self.client.force_authenticate(user=self.guardian)
		payload = {
			'team_id': str(self.team.id),
			'name': 'Should Fail',
			'start_date': '2026-03-01',
			'end_date': '2026-03-31',
		}
		res = self.client.post('/api/v1/campaigns/', payload, format='json')
		self.assertEqual(res.status_code, 403)
		self.assertEqual(Campaign.objects.filter(team=self.team).count(), 0)

	def test_active_campaign_returns_active_for_guardian_team(self):
		Campaign.objects.create(
			team=self.team,
			name='Active',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=10,
			buyout_amount_per_child='0.00',
			currency='SEK',
			is_active=True,
		)

		self.client.force_authenticate(user=self.guardian)
		res = self.client.get('/api/v1/campaigns/active/')
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['name'], 'Active')


class ChildrenApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()
		self.coach = User.objects.create_user(email='coach2@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian_a = User.objects.create_user(
			email='guardian-a@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_b = User.objects.create_user(
			email='guardian-b@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.child_a = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_b = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')
		GuardianChildLink.objects.create(guardian=self.guardian_a, child=self.child_a, relationship='parent')
		GuardianChildLink.objects.create(guardian=self.guardian_b, child=self.child_b, relationship='parent')

	def test_guardian_only_sees_linked_children(self):
		self.client.force_authenticate(user=self.guardian_a)
		res = self.client.get('/api/v1/children/')
		self.assertEqual(res.status_code, 200)
		ids = {row['id'] for row in res.data}
		self.assertEqual(ids, {str(self.child_a.id)})

	def test_coach_cannot_list_children(self):
		self.client.force_authenticate(user=self.coach)
		res = self.client.get('/api/v1/children/')
		self.assertEqual(res.status_code, 403)


class ChildCampaignTargetApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()
		self.coach = User.objects.create_user(email='coach3@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)

		self.guardian = User.objects.create_user(
			email='guardian-target@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_other = User.objects.create_user(
			email='guardian-target-other@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.child = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_other = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')
		GuardianChildLink.objects.create(guardian=self.guardian, child=self.child, relationship='parent')

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Active',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=20,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)

	def test_defaults_to_campaign_values_when_no_override(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/children/{self.child.id}/target/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['target_units'], 20)
		self.assertEqual(res.data['buyout_amount'], '1000.00')
		self.assertEqual(res.data['has_paid_buyout'], False)
		self.assertEqual(res.data['resolved_from'], 'campaign')

	def test_uses_child_override_when_present(self):
		ChildCampaignTarget.objects.create(
			child=self.child,
			campaign=self.campaign,
			target_units=30,
			buyout_amount='500.00',
			has_paid_buyout=True,
		)

		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/children/{self.child.id}/target/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['target_units'], 30)
		self.assertEqual(res.data['buyout_amount'], '500.00')
		self.assertEqual(res.data['has_paid_buyout'], True)
		self.assertEqual(res.data['resolved_from'], 'child')

	def test_guardian_cannot_access_unlinked_child(self):
		self.client.force_authenticate(user=self.guardian_other)
		url = f'/api/v1/campaigns/{self.campaign.id}/children/{self.child.id}/target/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 404)

	def test_coach_can_access_any_team_child(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/children/{self.child_other.id}/target/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['target_units'], 20)


class ProductApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-products@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian = User.objects.create_user(
			email='guardian-products@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=20,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)

		self.product_active = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit='10.00',
			is_active=True,
		)
		self.product_inactive = Product.objects.create(
			campaign=self.campaign,
			name='Old Product',
			description='',
			unit_price='1.00',
			profit_per_unit=None,
			is_active=False,
		)

	def test_guardian_can_list_active_products_only(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/products/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		ids = {row['id'] for row in res.data}
		self.assertEqual(ids, {str(self.product_active.id)})

	def test_guardian_cannot_create_product(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/products/'
		payload = {
			'name': 'New',
			'unit_price': '20.00',
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 403)

	def test_coach_can_create_product(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/products/'
		payload = {
			'name': 'Cheese',
			'description': 'Nice',
			'unit_price': '25.00',
			'profit_per_unit': '5.00',
			'is_active': True,
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 201)
		self.assertEqual(res.data['name'], 'Cheese')
		self.assertEqual(str(res.data['campaign']), str(self.campaign.id))

	def test_coach_can_patch_product(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/products/{self.product_active.id}/'
		res = self.client.patch(url, {'is_active': False}, format='json')
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['is_active'], False)

	def test_guardian_cannot_patch_product(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/products/{self.product_active.id}/'
		res = self.client.patch(url, {'is_active': False}, format='json')
		self.assertEqual(res.status_code, 403)


class SaleApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-sales@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian = User.objects.create_user(
			email='guardian-sales@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_other = User.objects.create_user(
			email='guardian-sales-other@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=20,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)
		self.child = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_other = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')
		GuardianChildLink.objects.create(guardian=self.guardian, child=self.child, relationship='parent')

		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)

	def test_guardian_can_create_sale_for_linked_child(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/'
		payload = {
			'child_id': str(self.child.id),
			'product_id': str(self.product.id),
			'quantity': 3,
			'buyer_name': 'Grandma',
			'is_paid': True,
			'is_delivered': False,
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 201)
		self.assertEqual(res.data['quantity'], 3)
		self.assertEqual(res.data['total_price'], '150.00')
		self.assertEqual(Sale.objects.count(), 1)

	def test_guardian_cannot_create_sale_for_unlinked_child(self):
		self.client.force_authenticate(user=self.guardian_other)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/'
		payload = {
			'child_id': str(self.child.id),
			'product_id': str(self.product.id),
			'quantity': 1,
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 404)

	def test_coach_can_create_sale_for_any_team_child(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/'
		payload = {
			'child_id': str(self.child_other.id),
			'product_id': str(self.product.id),
			'quantity': 2,
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 201)
		self.assertEqual(res.data['total_price'], '100.00')

	def test_quantity_must_be_positive(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/'
		payload = {
			'child_id': str(self.child.id),
			'product_id': str(self.product.id),
			'quantity': 0,
		}
		res = self.client.post(url, payload, format='json')
		self.assertEqual(res.status_code, 400)


class SaleListingApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-sales-list@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian_a = User.objects.create_user(
			email='guardian-sales-list-a@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_b = User.objects.create_user(
			email='guardian-sales-list-b@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=20,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)
		self.child_a = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_b = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')
		GuardianChildLink.objects.create(guardian=self.guardian_a, child=self.child_a, relationship='parent')
		GuardianChildLink.objects.create(guardian=self.guardian_b, child=self.child_b, relationship='parent')

		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)

		Sale.objects.create(
			campaign=self.campaign,
			child=self.child_a,
			product=self.product,
			quantity=2,
			buyer_name='A',
			is_paid=False,
			is_delivered=False,
			recorded_by=self.guardian_a,
		)
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child_b,
			product=self.product,
			quantity=3,
			buyer_name='B',
			is_paid=True,
			is_delivered=True,
			recorded_by=self.guardian_b,
		)

	def test_guardian_only_sees_sales_for_linked_children(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/my-children/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(len(res.data), 1)
		row = res.data[0]
		self.assertEqual(row['child_id'], str(self.child_a.id))
		self.assertEqual(row['product_name'], 'Salami')
		self.assertEqual(row['quantity'], 2)
		self.assertEqual(row['total_price'], '100.00')
		self.assertEqual(row['is_paid'], False)
		self.assertEqual(row['is_delivered'], False)

	def test_coach_cannot_use_my_children_endpoint(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/my-children/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 403)

	def test_child_filter_requires_link(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/campaigns/{self.campaign.id}/sales/my-children/?child_id={self.child_b.id}'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 404)


class SaleUpdateDeleteApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-sales-edit@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian_a = User.objects.create_user(
			email='guardian-sales-edit-a@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_b = User.objects.create_user(
			email='guardian-sales-edit-b@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=20,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)
		self.child = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		GuardianChildLink.objects.create(guardian=self.guardian_a, child=self.child, relationship='parent')

		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)

		self.sale = Sale.objects.create(
			campaign=self.campaign,
			child=self.child,
			product=self.product,
			quantity=2,
			buyer_name='X',
			is_paid=False,
			is_delivered=False,
			recorded_by=self.guardian_a,
		)

	def test_creator_guardian_can_patch_quantity_and_total_recalculates(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.patch(url, {'quantity': 3}, format='json')
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['quantity'], 3)
		self.assertEqual(res.data['total_price'], '150.00')

	def test_creator_guardian_can_patch_flags(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.patch(url, {'is_paid': True, 'is_delivered': True}, format='json')
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['is_paid'], True)
		self.assertEqual(res.data['is_delivered'], True)

	def test_other_guardian_cannot_patch_sale(self):
		self.client.force_authenticate(user=self.guardian_b)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.patch(url, {'quantity': 3}, format='json')
		self.assertEqual(res.status_code, 404)

	def test_coach_can_patch_sale(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.patch(url, {'quantity': 4}, format='json')
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['total_price'], '200.00')

	def test_quantity_must_be_positive_on_patch(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.patch(url, {'quantity': 0}, format='json')
		self.assertEqual(res.status_code, 400)

	def test_creator_guardian_can_delete_sale(self):
		self.client.force_authenticate(user=self.guardian_a)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.delete(url)
		self.assertEqual(res.status_code, 204)
		self.assertEqual(Sale.objects.filter(id=self.sale.id).count(), 0)

	def test_other_guardian_cannot_delete_sale(self):
		self.client.force_authenticate(user=self.guardian_b)
		url = f'/api/v1/sales/{self.sale.id}/'
		res = self.client.delete(url)
		self.assertEqual(res.status_code, 404)


class ChildCampaignSummaryApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-summary@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian = User.objects.create_user(
			email='guardian-summary@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)
		self.guardian_other = User.objects.create_user(
			email='guardian-summary-other@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=10,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)
		self.child = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_other = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')
		GuardianChildLink.objects.create(guardian=self.guardian, child=self.child, relationship='parent')

		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)

		# two sales: 2 + 1 units => 3 units sold, 150.00 total
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child,
			product=self.product,
			quantity=2,
			buyer_name='A',
			is_paid=False,
			is_delivered=False,
			recorded_by=self.guardian,
		)
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child,
			product=self.product,
			quantity=1,
			buyer_name='B',
			is_paid=True,
			is_delivered=False,
			recorded_by=self.guardian,
		)

	def test_guardian_can_get_summary_for_linked_child(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/children/{self.child.id}/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['target_units'], 10)
		self.assertEqual(res.data['total_units_sold'], 3)
		self.assertEqual(res.data['total_sales_amount'], '150.00')
		self.assertEqual(res.data['remaining_units_to_target'], 7)
		self.assertEqual(res.data['progress_percent'], '30.00')

	def test_child_override_target_affects_progress(self):
		ChildCampaignTarget.objects.create(child=self.child, campaign=self.campaign, target_units=4)
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/children/{self.child.id}/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['target_units'], 4)
		self.assertEqual(res.data['remaining_units_to_target'], 1)
		self.assertEqual(res.data['progress_percent'], '75.00')

	def test_guardian_cannot_get_summary_for_unlinked_child(self):
		self.client.force_authenticate(user=self.guardian_other)
		url = f'/api/v1/children/{self.child.id}/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 404)

	def test_coach_can_get_summary_for_any_team_child(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/children/{self.child_other.id}/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['total_units_sold'], 0)


class TeamCampaignSummaryApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(
			email='coach-team-summary@example.com',
			password='pass',
			role='coach',
		)
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)

		self.guardian = User.objects.create_user(
			email='guardian-team-summary@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.other_coach = User.objects.create_user(
			email='coach-team-summary-other@example.com',
			password='pass',
			role='coach',
		)
		self.other_team = Team.objects.create(name='P12 Red', club_name='Other Club', coach=self.other_coach)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=10,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)

		self.child_a = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.child_b = Child.objects.create(team=self.team, first_name='Erik', last_initial='B')

		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)

		# 3 units sold for Lisa A
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child_a,
			product=self.product,
			quantity=2,
			buyer_name='A',
			is_paid=False,
			is_delivered=False,
			recorded_by=self.guardian,
		)
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child_a,
			product=self.product,
			quantity=1,
			buyer_name='B',
			is_paid=True,
			is_delivered=False,
			recorded_by=self.guardian,
		)

	def test_guardian_can_get_team_campaign_summary(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/team/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)

		self.assertEqual(res.data['campaign']['id'], str(self.campaign.id))
		self.assertEqual(res.data['team']['id'], str(self.team.id))
		self.assertEqual(res.data['team_total_units_sold'], 3)
		self.assertEqual(res.data['team_target_units'], 20)
		self.assertEqual(res.data['team_progress_percent'], '15.00')

		children = res.data['children']
		self.assertEqual(len(children), 2)
		# Ensure privacy: no buyer details
		self.assertFalse(any('buyer_name' in c for c in children))

		by_name = {c['name']: c for c in children}
		self.assertEqual(by_name['Lisa A']['target_units'], 10)
		self.assertEqual(by_name['Lisa A']['total_units_sold'], 3)
		self.assertEqual(by_name['Lisa A']['progress_percent'], '30.00')
		self.assertEqual(by_name['Erik B']['total_units_sold'], 0)
		self.assertEqual(by_name['Erik B']['progress_percent'], '0.00')

	def test_child_target_override_affects_team_totals(self):
		ChildCampaignTarget.objects.create(child=self.child_a, campaign=self.campaign, target_units=4)
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/team/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data['team_target_units'], 14)
		self.assertEqual(res.data['team_progress_percent'], '21.43')

		by_name = {c['name']: c for c in res.data['children']}
		self.assertEqual(by_name['Lisa A']['target_units'], 4)
		self.assertEqual(by_name['Lisa A']['progress_percent'], '75.00')

	def test_other_team_coach_cannot_access_campaign_summary(self):
		self.client.force_authenticate(user=self.other_coach)
		url = f'/api/v1/team/campaigns/{self.campaign.id}/summary/'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 404)


class CampaignExportCsvApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		User = get_user_model()

		self.coach = User.objects.create_user(email='coach-export@example.com', password='pass', role='coach')
		self.team = Team.objects.create(name='P11 Blue', club_name='Test Club', coach=self.coach)
		self.guardian = User.objects.create_user(
			email='guardian-export@example.com',
			password='pass',
			role='guardian',
			team=self.team,
		)

		self.other_coach = User.objects.create_user(email='coach-export-other@example.com', password='pass', role='coach')
		self.other_team = Team.objects.create(name='P12 Red', club_name='Other Club', coach=self.other_coach)

		self.campaign = Campaign.objects.create(
			team=self.team,
			name='Campaign',
			description='',
			start_date='2026-01-01',
			end_date='2026-01-31',
			default_target_units_per_child=10,
			buyout_amount_per_child='1000.00',
			currency='SEK',
			is_active=True,
		)

		self.child = Child.objects.create(team=self.team, first_name='Lisa', last_initial='A')
		self.product = Product.objects.create(
			campaign=self.campaign,
			name='Salami',
			description='',
			unit_price='50.00',
			profit_per_unit=None,
			is_active=True,
		)
		Sale.objects.create(
			campaign=self.campaign,
			child=self.child,
			product=self.product,
			quantity=3,
			buyer_name='Grandma',
			is_paid=True,
			is_delivered=False,
			recorded_by=self.guardian,
		)

	def test_coach_can_export_csv_headers_and_rows(self):
		self.client.force_authenticate(user=self.coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/export/csv'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
		self.assertIn('text/csv', res['Content-Type'])

		body = res.content.decode('utf-8')
		lines = [ln for ln in body.splitlines() if ln.strip()]
		self.assertGreaterEqual(len(lines), 2)
		self.assertEqual(
			lines[0],
			'child_id,child_name,product_id,product_name,quantity,buyer_name,is_paid,is_delivered,total_price',
		)
		self.assertIn('Lisa A', lines[1])
		self.assertIn('Salami', lines[1])
		self.assertIn('Grandma', lines[1])
		self.assertIn(',true,false,150.00', lines[1])

	def test_guardian_cannot_export_csv(self):
		self.client.force_authenticate(user=self.guardian)
		url = f'/api/v1/campaigns/{self.campaign.id}/export/csv'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 403)

	def test_other_team_coach_gets_404_for_campaign(self):
		self.client.force_authenticate(user=self.other_coach)
		url = f'/api/v1/campaigns/{self.campaign.id}/export/csv'
		res = self.client.get(url)
		self.assertEqual(res.status_code, 404)
