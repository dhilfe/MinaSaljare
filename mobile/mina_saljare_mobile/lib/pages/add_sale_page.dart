import 'package:flutter/material.dart';

import '../api/api_client.dart';

class AddSalePage extends StatefulWidget {
  const AddSalePage({
    super.key,
    required this.api,
    required this.campaign,
    required this.child,
  });

  final ApiClient api;
  final CampaignDto campaign;
  final ChildDto child;

  @override
  State<AddSalePage> createState() => _AddSalePageState();
}

class _AddSalePageState extends State<AddSalePage> {
  bool _loading = false;
  String? _error;

  List<ProductDto> _products = const [];
  String? _productId;

  final _quantityController = TextEditingController(text: '1');
  final _buyerNameController = TextEditingController();
  bool _isPaid = false;
  bool _isDelivered = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _buyerNameController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final products = await widget.api.fetchProducts(
        campaignId: widget.campaign.id,
      );
      if (!mounted) return;
      setState(() {
        _products = products;
        _productId =
            _productId ?? (products.isNotEmpty ? products.first.id : null);
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

  Future<void> _save() async {
    final productId = _productId;
    if (productId == null) return;

    final quantity = int.tryParse(_quantityController.text.trim());
    if (quantity == null || quantity <= 0) {
      setState(() {
        _error = 'Quantity must be a positive number';
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final buyerName = _buyerNameController.text.trim();
      await widget.api.createSale(
        campaignId: widget.campaign.id,
        childId: widget.child.id,
        productId: productId,
        quantity: quantity,
        buyerName: buyerName.isEmpty ? null : buyerName,
        isPaid: _isPaid,
        isDelivered: _isDelivered,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
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
    return Scaffold(
      appBar: AppBar(title: const Text('Add Sale')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Child: ${widget.child.shortName}'),
            const SizedBox(height: 12),
            if (_loading) const Text('Loading…'),
            if (_error != null) Text('Error: $_error'),
            if (_products.isEmpty && !_loading)
              const Text('No products available.'),
            if (_products.isNotEmpty)
              DropdownButton<String>(
                value: _productId,
                isExpanded: true,
                items: _products
                    .map(
                      (p) => DropdownMenuItem<String>(
                        value: p.id,
                        child: Text('${p.name} (${p.unitPrice})'),
                      ),
                    )
                    .toList(growable: false),
                onChanged: _loading
                    ? null
                    : (v) => setState(() => _productId = v),
              ),
            const SizedBox(height: 12),
            TextField(
              controller: _quantityController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Quantity'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _buyerNameController,
              decoration: const InputDecoration(
                labelText: 'Buyer name (optional)',
              ),
            ),
            const SizedBox(height: 12),
            CheckboxListTile(
              value: _isPaid,
              onChanged: _loading
                  ? null
                  : (v) => setState(() => _isPaid = v ?? false),
              title: const Text('Paid'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            CheckboxListTile(
              value: _isDelivered,
              onChanged: _loading
                  ? null
                  : (v) => setState(() => _isDelivered = v ?? false),
              title: const Text('Delivered'),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: (_loading || _productId == null) ? null : _save,
                child: const Text('Save'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
