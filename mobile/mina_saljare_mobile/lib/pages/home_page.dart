import 'package:flutter/material.dart';

import '../api/api_client.dart';
import 'add_sale_page.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key, required this.api});

  final ApiClient api;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  bool _loading = false;
  String? _error;

  CampaignDto? _campaign;
  List<ChildDto> _children = const [];
  String? _selectedChildId;
  ChildCampaignSummaryDto? _summary;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final campaign = await widget.api.fetchActiveCampaign();
      final children = await widget.api.fetchChildren();
      final selectedId =
          _selectedChildId ?? (children.isNotEmpty ? children.first.id : null);
      ChildCampaignSummaryDto? summary;
      if (selectedId != null) {
        summary = await widget.api.fetchChildSummary(
          childId: selectedId,
          campaignId: campaign.id,
        );
      }

      if (!mounted) return;
      setState(() {
        _campaign = campaign;
        _children = children;
        _selectedChildId = selectedId;
        _summary = summary;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _selectChild(String childId) async {
    final campaign = _campaign;
    if (campaign == null) return;

    setState(() {
      _selectedChildId = childId;
      _loading = true;
      _error = null;
    });

    try {
      final summary = await widget.api.fetchChildSummary(
        childId: childId,
        campaignId: campaign.id,
      );
      if (!mounted) return;
      setState(() {
        _summary = summary;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final campaign = _campaign;
    final selectedChild = _children.firstWhereOrNull(
      (c) => c.id == _selectedChildId,
    );

    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (campaign != null) Text('Campaign: ${campaign.name}'),
            if (campaign == null && !_loading) const Text('No active campaign.'),
            const SizedBox(height: 12),
            if (_children.isNotEmpty)
              DropdownButton<String>(
                value: _selectedChildId,
                isExpanded: true,
                items: _children
                    .map(
                      (c) => DropdownMenuItem<String>(
                        value: c.id,
                        child: Text(c.shortName),
                      ),
                    )
                    .toList(growable: false),
                onChanged: _loading
                    ? null
                    : (value) {
                        if (value != null) _selectChild(value);
                      },
              ),
            if (_children.isEmpty && !_loading)
              const Text('No linked children found.'),
            const SizedBox(height: 12),
            if (_loading) const Text('Loading…'),
            if (_error != null) Text('Error: $_error'),
            if (_summary != null) _ProgressCard(summary: _summary!),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: (_loading || campaign == null || selectedChild == null)
                    ? null
                    : () async {
                        final saved = await Navigator.of(context).push<bool>(
                          MaterialPageRoute(
                            builder: (_) => AddSalePage(
                              api: widget.api,
                              campaign: campaign,
                              child: selectedChild,
                            ),
                          ),
                        );
                        if (saved == true) {
                          await _load();
                          if (!context.mounted) return;
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Sale saved')),
                          );
                        }
                      },
                child: const Text('Add Sale'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressCard extends StatelessWidget {
  const _ProgressCard({required this.summary});

  final ChildCampaignSummaryDto summary;

  @override
  Widget build(BuildContext context) {
    final progress = (summary.progressPercent / 100).clamp(0.0, 1.0);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Sold: ${summary.totalUnitsSold} / ${summary.targetUnits}'),
            const SizedBox(height: 6),
            LinearProgressIndicator(value: progress),
            const SizedBox(height: 10),
            Text('Remaining: ${summary.remainingUnitsToTarget}'),
            Text('Sales amount: ${summary.totalSalesAmount}'),
          ],
        ),
      ),
    );
  }
}

extension<T> on Iterable<T> {
  T? firstWhereOrNull(bool Function(T element) test) {
    for (final element in this) {
      if (test(element)) return element;
    }
    return null;
  }
}
