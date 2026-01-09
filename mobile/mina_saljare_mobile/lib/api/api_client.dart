import 'dart:convert';

import 'package:http/http.dart' as http;

import '../auth/token_storage.dart';
import '../config/app_config.dart';

class CampaignDto {
  CampaignDto({
    required this.id,
    required this.name,
    required this.currency,
    this.endDate,
  });

  final String id;
  final String name;
  final String currency;
  final String? endDate;

  static CampaignDto fromJson(Map<String, dynamic> json) {
    return CampaignDto(
      id: json['id'] as String,
      name: json['name'] as String,
      currency: (json['currency'] as String?) ?? 'SEK',
      endDate: json['end_date'] as String?,
    );
  }
}

class TeamChildSummaryDto {
  TeamChildSummaryDto({
    required this.id,
    required this.name,
    required this.targetUnits,
    required this.totalUnitsSold,
    required this.progressPercent,
  });

  final String id;
  final String name;
  final int targetUnits;
  final int totalUnitsSold;
  final double progressPercent;

  static TeamChildSummaryDto fromJson(Map<String, dynamic> json) {
    return TeamChildSummaryDto(
      id: json['id'] as String,
      name: json['name'] as String,
      targetUnits: json['target_units'] as int,
      totalUnitsSold: json['total_units_sold'] as int,
      progressPercent: double.tryParse(json['progress_percent'].toString()) ?? 0.0,
    );
  }
}

class TeamCampaignSummaryDto {
  TeamCampaignSummaryDto({
    required this.teamName,
    required this.campaignName,
    required this.children,
    required this.teamTotalUnitsSold,
    required this.teamTargetUnits,
  });

  final String teamName;
  final String campaignName;
  final List<TeamChildSummaryDto> children;
  final int teamTotalUnitsSold;
  final int teamTargetUnits;

  static TeamCampaignSummaryDto fromJson(Map<String, dynamic> json) {
    final team = json['team'] as Map<String, dynamic>;
    final campaign = json['campaign'] as Map<String, dynamic>;
    final childrenRaw = (json['children'] as List).whereType<Map<String, dynamic>>();

    return TeamCampaignSummaryDto(
      teamName: team['name'] as String,
      campaignName: campaign['name'] as String,
      children: childrenRaw.map(TeamChildSummaryDto.fromJson).toList(growable: false),
      teamTotalUnitsSold: json['team_total_units_sold'] as int,
      teamTargetUnits: json['team_target_units'] as int,
    );
  }
}

class ChildDto {
  ChildDto({
    required this.id,
    required this.firstName,
    required this.lastInitial,
    required this.shirtNumber,
  });

  final String id;
  final String firstName;
  final String? lastInitial;
  final int? shirtNumber;

  String get shortName => lastInitial == null || lastInitial!.isEmpty
      ? firstName
      : '$firstName ${lastInitial!}';

  static ChildDto fromJson(Map<String, dynamic> json) {
    return ChildDto(
      id: json['id'] as String,
      firstName: json['first_name'] as String,
      lastInitial: json['last_initial'] as String?,
      shirtNumber: json['shirt_number'] as int?,
    );
  }
}

class ProductDto {
  ProductDto({required this.id, required this.name, required this.unitPrice});

  final String id;
  final String name;
  final String unitPrice;

  static ProductDto fromJson(Map<String, dynamic> json) {
    return ProductDto(
      id: json['id'] as String,
      name: json['name'] as String,
      unitPrice: json['unit_price'].toString(),
    );
  }
}

class ChildCampaignSummaryDto {
  ChildCampaignSummaryDto({
    required this.targetUnits,
    required this.totalUnitsSold,
    required this.totalSalesAmount,
    required this.remainingUnitsToTarget,
    required this.progressPercent,
  });

  final int targetUnits;
  final int totalUnitsSold;
  final String totalSalesAmount;
  final int remainingUnitsToTarget;
  final double progressPercent;

  static ChildCampaignSummaryDto fromJson(Map<String, dynamic> json) {
    return ChildCampaignSummaryDto(
      targetUnits: json['target_units'] as int,
      totalUnitsSold: json['total_units_sold'] as int,
      totalSalesAmount: json['total_sales_amount'].toString(),
      remainingUnitsToTarget: json['remaining_units_to_target'] as int,
      progressPercent: double.tryParse(json['progress_percent'].toString()) ?? 0.0,
    );
  }
}

class ApiClient {
  ApiClient({http.Client? httpClient, AccessTokenStore? tokenStore})
      : _httpClient = httpClient ?? http.Client(),
        _tokenStore = tokenStore;

  final http.Client _httpClient;
  final AccessTokenStore? _tokenStore;

  Uri _uri(String path) {
    final base = AppConfig.apiBaseUrl.replaceAll(RegExp(r'/*$'), '');
    final p = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$base$p');
  }

  Future<String> fetchHealthStatus() async {
    final response = await _httpClient.get(_uri('/health/'));
    if (response.statusCode != 200) {
      throw Exception('Health check failed (${response.statusCode})');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'];
    if (status is String) return status;
    throw Exception('Unexpected health response');
  }

  Future<String> login({
    required String email,
    required String password,
  }) async {
    final response = await _httpClient.post(
      _uri('/v1/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode != 200) {
      throw Exception('Login failed (${response.statusCode})');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['access_token'];
    if (token is String && token.isNotEmpty) return token;
    throw Exception('Unexpected login response');
  }

  Future<CampaignDto> fetchActiveCampaign() async {
    final data = await _getJson('/v1/campaigns/active/');
    return CampaignDto.fromJson(data);
  }

  Future<TeamCampaignSummaryDto> fetchTeamCampaignSummary({
    required String campaignId,
  }) async {
    final data = await _getJson('/v1/team/campaigns/$campaignId/summary/');
    return TeamCampaignSummaryDto.fromJson(data);
  }

  Future<List<ChildDto>> fetchChildren() async {
    final data = await _getJsonList('/v1/children/');
    return data.map(ChildDto.fromJson).toList(growable: false);
  }

  Future<ChildCampaignSummaryDto> fetchChildSummary({
    required String childId,
    required String campaignId,
  }) async {
    final data = await _getJson(
      '/v1/children/$childId/campaigns/$campaignId/summary/',
    );
    return ChildCampaignSummaryDto.fromJson(data);
  }

  Future<List<ProductDto>> fetchProducts({required String campaignId}) async {
    final data = await _getJsonList('/v1/campaigns/$campaignId/products/');
    return data.map(ProductDto.fromJson).toList(growable: false);
  }

  Future<void> createSale({
    required String campaignId,
    required String childId,
    required String productId,
    required int quantity,
    String? buyerName,
    required bool isPaid,
    required bool isDelivered,
  }) async {
    final response = await _httpClient.post(
      _uri('/v1/campaigns/$campaignId/sales/'),
      headers: await _authHeaders(json: true),
      body: jsonEncode({
        'child_id': childId,
        'product_id': productId,
        'quantity': quantity,
        if (buyerName != null) 'buyer_name': buyerName,
        'is_paid': isPaid,
        'is_delivered': isDelivered,
      }),
    );
    if (response.statusCode != 201) {
      throw Exception('Create sale failed (${response.statusCode})');
    }
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final response = await _httpClient.get(
      _uri(path),
      headers: await _authHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Request failed (${response.statusCode})');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is Map<String, dynamic>) return decoded;
    throw Exception('Unexpected response');
  }

  Future<List<Map<String, dynamic>>> _getJsonList(String path) async {
    final response = await _httpClient.get(
      _uri(path),
      headers: await _authHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Request failed (${response.statusCode})');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is List) {
      return decoded.whereType<Map<String, dynamic>>().toList(growable: false);
    }
    throw Exception('Unexpected response');
  }

  Future<Map<String, String>> _authHeaders({bool json = false}) async {
    final store = _tokenStore;
    if (store == null) {
      return json ? {'Content-Type': 'application/json'} : <String, String>{};
    }

    final token = await store.readAccessToken();
    if (token == null || token.isEmpty) {
      return json ? {'Content-Type': 'application/json'} : <String, String>{};
    }

    final headers = <String, String>{'Authorization': 'Bearer $token'};
    if (json) headers['Content-Type'] = 'application/json';
    return headers;
  }
}
