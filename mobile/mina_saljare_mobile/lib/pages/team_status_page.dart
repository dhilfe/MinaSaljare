import 'package:flutter/material.dart';

import '../api/api_client.dart';

class TeamStatusPage extends StatefulWidget {
  const TeamStatusPage({super.key, required this.api});

  final ApiClient api;

  @override
  State<TeamStatusPage> createState() => _TeamStatusPageState();
}

class _TeamStatusPageState extends State<TeamStatusPage> {
  bool _loading = false;
  String? _error;

  CampaignDto? _campaign;
  TeamCampaignSummaryDto? _summary;

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
      final summary = await widget.api.fetchTeamCampaignSummary(
        campaignId: campaign.id,
      );
      if (!mounted) return;
      setState(() {
        _campaign = campaign;
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
    final summary = _summary;

    return Scaffold(
      appBar: AppBar(title: const Text('Team Status')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (campaign != null) ...[
              Text('Campaign: ${campaign.name}'),
              if (campaign.endDate != null) Text('Ends: ${campaign.endDate}'),
            ],
            const SizedBox(height: 12),
            if (_loading) const Text('Loading…'),
            if (_error != null) Text('Error: $_error'),
            if (summary != null) ...[
              Text(
                'Team: ${summary.teamName} — ${summary.teamTotalUnitsSold} / ${summary.teamTargetUnits}',
              ),
              const SizedBox(height: 8),
              Expanded(
                child: ListView.separated(
                  itemCount: summary.children.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final child = summary.children[index];
                    final progress =
                        (child.progressPercent / 100).clamp(0.0, 1.0);
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              child.name,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 6),
                            Text(
                              '${child.totalUnitsSold} / ${child.targetUnits} units',
                            ),
                            const SizedBox(height: 6),
                            LinearProgressIndicator(value: progress),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
