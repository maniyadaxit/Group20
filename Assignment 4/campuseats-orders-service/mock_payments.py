# NOTE: This is a minimal stand-in for your actual Tutorial 4 Payments
# service so this Orders service can be run and demonstrated end-to-end.
# Replace PAYMENTS_SERVICE_URL with your real Payments service's address
# when you run this for real — do not submit this file as your Payments
# service.

from flask import Flask, request, jsonify

app = Flask(__name__)
seen_keys = {}


@app.route("/payments", methods=["POST"])
def create_payment():
    key = request.headers.get("Idempotency-Key")
    if key and key in seen_keys:
        return jsonify(seen_keys[key]), 200
    body = request.get_json()
    result = {"paymentId": f"PAY-{len(seen_keys) + 1:05d}", "status": "SUCCESS", "amount": body.get("amount")}
    if key:
        seen_keys[key] = result
    return jsonify(result), 201


if __name__ == "__main__":
    app.run(port=6001)
