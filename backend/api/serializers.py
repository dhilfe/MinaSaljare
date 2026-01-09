from rest_framework import serializers

from core.models import Campaign, Child, Product, Sale, Team


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name', 'club_name')


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = (
            'id',
            'team',
            'name',
            'description',
            'start_date',
            'end_date',
            'default_target_units_per_child',
            'buyout_amount_per_child',
            'currency',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ChildTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name')


class ChildSerializer(serializers.ModelSerializer):
    team = ChildTeamSerializer(read_only=True)

    class Meta:
        model = Child
        fields = (
            'id',
            'first_name',
            'last_initial',
            'shirt_number',
            'is_active',
            'team',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ResolvedChildCampaignTargetSerializer(serializers.Serializer):
    child_id = serializers.UUIDField()
    campaign_id = serializers.UUIDField()
    target_units = serializers.IntegerField()
    buyout_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    has_paid_buyout = serializers.BooleanField()
    resolved_from = serializers.ChoiceField(choices=('campaign', 'child'))


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id',
            'campaign',
            'name',
            'description',
            'unit_price',
            'profit_per_unit',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = (
            'id',
            'campaign',
            'child',
            'product',
            'quantity',
            'total_price',
            'buyer_name',
            'is_paid',
            'is_delivered',
            'recorded_by',
            'recorded_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'total_price', 'recorded_by', 'created_at', 'updated_at')


class SaleCreateSerializer(serializers.Serializer):
    child_id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField()
    buyer_name = serializers.CharField(required=False, allow_blank=True)
    is_paid = serializers.BooleanField(required=False)
    is_delivered = serializers.BooleanField(required=False)


class SaleUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=False)
    is_paid = serializers.BooleanField(required=False)
    is_delivered = serializers.BooleanField(required=False)


class ChildCampaignSummarySerializer(serializers.Serializer):
    child_id = serializers.UUIDField()
    campaign_id = serializers.UUIDField()
    target_units = serializers.IntegerField()
    total_units_sold = serializers.IntegerField()
    total_sales_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_units_to_target = serializers.IntegerField()
    progress_percent = serializers.DecimalField(max_digits=6, decimal_places=2)


class TeamSummaryTeamSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class TeamSummaryCampaignSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class TeamCampaignChildSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    target_units = serializers.IntegerField()
    total_units_sold = serializers.IntegerField()
    progress_percent = serializers.DecimalField(max_digits=6, decimal_places=2)


class TeamCampaignSummarySerializer(serializers.Serializer):
    campaign = TeamSummaryCampaignSerializer()
    team = TeamSummaryTeamSerializer()
    children = TeamCampaignChildSummarySerializer(many=True)
    team_total_units_sold = serializers.IntegerField()
    team_target_units = serializers.IntegerField()
    team_progress_percent = serializers.DecimalField(max_digits=6, decimal_places=2)


class SaleListItemSerializer(serializers.ModelSerializer):
    child_id = serializers.UUIDField(source='child.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Sale
        fields = (
            'id',
            'child_id',
            'product_name',
            'quantity',
            'total_price',
            'is_paid',
            'is_delivered',
        )
