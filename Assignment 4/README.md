# CampusEats - Assignment 4

## Assignment overview

This folder contains design and integration artifacts for CampusEats, a campus food-ordering system. It documents the domain model, sample HTTP traffic, network analysis, data schema, service boundaries, and a SOAP payment-gateway contract. It is a design/integration package, not a complete deployed full-stack application.

## Team

| Name | Roll number |
|---|---|
| Daxit Maniya | 20251651054 |
| Ethasam | 20251651038 |
| Gulshan Kumar | 20251651040 |

## Artifact map

| Path | Purpose |
|---|---|
| `docs/brief.md` | Domain actors, entities, and service actions |
| `docs/http-log.md` | HTTP request/response examples and analysis |
| `docs/network-analysis.md` | Browser Network-panel observations |
| `docs/screenshots/` | Five request evidence screenshots |
| `design/design.pdf` | Main system design document |
| `schema/schema.sql` | Data-definition script for the design |
| `schema/schema.drawio`, `schema/schema.png` | Editable and exported schema diagram |
| `services/services.drawio`, `services/services.png` | Editable and exported service architecture |
| `integration/integration.pdf` | SOAP/HTTP integration and error-mapping design |
| `partner/partner.wsdl` | Payment gateway SOAP contract |
| `soap/soap-request.xml` | Sample charge request; credentials are placeholders |
| `soap/soap-response.xml` | Sample successful response |
| `soap/soap-fault.xml` | Sample fault response |

## Design overview

The model covers users, delivery addresses, merchants, menu items, carts, orders, order items, payments, deliveries, message logs, refunds, riders, and rider assignments. The service diagram and schema are intended to illustrate separation of concerns and the relationships needed by the CampusEats workflow.

The payment integration examples demonstrate a typed SOAP contract, request header, successful charge response, and failure response. The XML request is a non-functional example. Do not place real API keys or payment tokens in source control.

## Review before submission

1. Open the PDF design documents and both exported diagrams to confirm they render correctly.
2. Verify the SQL dialect against the database selected for any live execution.
3. Check the HTTP logs and screenshots against the original Assignment 4 handout.
4. Keep all credentials fictional. If any repository value was ever a genuine secret, revoke/rotate it with the provider.
