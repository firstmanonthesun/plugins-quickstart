import json
import requests
import urllib.parse
import quart
import quart_cors
from quart import request
from datetime import datetime


lenTarget = 5000

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
headers = {
    "Authorization": "Basic S3lKWmR2V3NLd2FSWkljRnM5WFlCTGJJcjgyMmlmY2pCZ0tKWHpiSQ=="
}

@app.get("/companies")
async def get_companies():
    res = requests.get(
        "https://api.codat.io/companies", headers=headers)
    body = res.json()
    return quart.Response(response=json.dumps(body), status=200)

@app.get("/invoices")
async def get_invoices():
    print(f"REQ: {request}")
    companyId = request.args.get("companyId")
    query = request.args.get("query")
    orderBy = request.args.get("orderBy")
    pageSize = request.args.get("pageSize")

    queryText = "" if not query else f"query={urllib.parse.quote(query)}&"
    orderByText = "" if not orderBy else f"orderBy={urllib.parse.quote(orderBy)}&"
    pageSizeText = "" if not pageSize else f"pageSize={pageSize}"
    
    url = f"https://api.codat.io/companies/{companyId}/data/invoices?{queryText}{orderByText}{pageSizeText}"
    print(f"URL: {url}")
    res = requests.get(url, headers=headers)
    body = res.json()

    result = minify_invoices(json.dumps(body))
    return quart.Response(response=result, status=200)

def minify_invoices(json_string):
    if len(json_string) > lenTarget:
        json_string = remove_nodes(json_string, ['lineItems'])
        if len(json_string) > lenTarget:
            json_string = remove_nodes(json_string, ['sourceModifiedDate', 'modifiedDate'])
            if len(json_string) > lenTarget:
                json_string = remove_nodes(json_string, ['paymentAllocations', 'salesOrderRefs'])
                if len(json_string) > lenTarget:
                    json_string = remove_nodes(json_string, ['additionalTaxAmount', 'additionalTaxPercentage', 'withholdingTax'])
                    if len(json_string) > lenTarget:
                        json_string = remove_nodes(json_string, ['customerRef'])
                        if len(json_string) > lenTarget:
                            json_string = aggregate_results_invoices(json_string)
    return json_string

def aggregate_results_invoices(json_string):
    data = json.loads(json_string)

    total_discount = 0
    total_subTotal = 0
    total_taxAmount = 0
    total_amount = 0
    total_amountDue = 0
    total_discountPercentage = 0
    currency = "USD"
    total_count = 0

    earliest_issueDate = datetime.max
    latest_issueDate = datetime.min
    earliest_dueDate = datetime.max
    latest_dueDate = datetime.min

    for item in data['results']:
        total_discount += item['totalDiscount']
        total_subTotal += item['subTotal']
        total_taxAmount += item['totalTaxAmount']
        total_amount += item['totalAmount']
        total_amountDue += item['amountDue']
        total_discountPercentage += item['discountPercentage']
        currency = item['currency']
        total_count += 1

        issueDate = datetime.fromisoformat(item['issueDate'].replace('Z', '+00:00'))
        dueDate = datetime.fromisoformat(item['dueDate'].replace('Z', '+00:00'))

        earliest_issueDate = min(earliest_issueDate, issueDate)
        latest_issueDate = max(latest_issueDate, issueDate)
        earliest_dueDate = min(earliest_dueDate, dueDate)
        latest_dueDate = max(latest_dueDate, dueDate)

    aggregated_data = {
        'currency': currency,
        'totalDiscount': total_discount,
        'subTotal': total_subTotal,
        'totalTaxAmount': total_taxAmount,
        'totalAmount': total_amount,
        'amountDue': total_amountDue,
        'averageDiscountPercentage': total_discountPercentage / total_count if total_count > 0 else 0,
        'totalCount': total_count,
        'earliestIssueDate': earliest_issueDate.isoformat(),
        'latestIssueDate': latest_issueDate.isoformat(),
        'earliestDueDate': earliest_dueDate.isoformat(),
        'latestDueDate': latest_dueDate.isoformat()
    }

    return json.dumps(aggregated_data)

@app.get("/bills")
async def get_bills():
    print(f"REQ: {request}")
    companyId = request.args.get("companyId")
    query = request.args.get("query")
    orderBy = request.args.get("orderBy")
    pageSize = request.args.get("pageSize")

    queryText = "" if not query else f"query={urllib.parse.quote(query)}&"
    orderByText = "" if not orderBy else f"orderBy={urllib.parse.quote(orderBy)}&"
    pageSizeText = "" if not pageSize else f"pageSize={pageSize}"
    
    url = f"https://api.codat.io/companies/{companyId}/data/bills?{queryText}{orderByText}{pageSizeText}"
    print(f"URL: {url}")
    res = requests.get(url, headers=headers)
    body = res.json()

    result = minify_bills(json.dumps(body))
    return quart.Response(response=result, status=200)

def minify_bills(json_string):
    if len(json_string) > lenTarget:
        json_string = remove_nodes(json_string, ['lineItems'])
        if len(json_string) > lenTarget:
            json_string = remove_nodes(json_string, ['sourceModifiedDate', 'modifiedDate'])
            if len(json_string) > lenTarget:
                json_string = remove_nodes(json_string, ['paymentAllocations', 'purchaseOrderRefs'])
                if len(json_string) > lenTarget:
                    json_string = remove_nodes(json_string, ['additionalTaxAmount', 'additionalTaxPercentage', 'withholdingTax'])
                    if len(json_string) > lenTarget:
                        json_string = remove_nodes(json_string, ['supplierRef'])
                        if len(json_string) > lenTarget:
                            json_string = aggregate_results_bills(json_string)
    return json_string

def aggregate_results_bills(json_string):
    data = json.loads(json_string)

    total_subTotal = 0
    total_taxAmount = 0
    total_amount = 0
    total_amountDue = 0
    currency = "USD"
    total_count = 0

    earliest_issueDate = datetime.max
    latest_issueDate = datetime.min
    earliest_dueDate = datetime.max
    latest_dueDate = datetime.min

    for item in data['results']:
        total_subTotal += item['subTotal']
        total_taxAmount += item['taxAmount']
        total_amount += item['totalAmount']
        total_amountDue += item['amountDue']
        currency = item['currency']
        total_count += 1

        issueDate = datetime.fromisoformat(item['issueDate'].replace('Z', '+00:00'))
        dueDate = datetime.fromisoformat(item['dueDate'].replace('Z', '+00:00'))

        earliest_issueDate = min(earliest_issueDate, issueDate)
        latest_issueDate = max(latest_issueDate, issueDate)
        earliest_dueDate = min(earliest_dueDate, dueDate)
        latest_dueDate = max(latest_dueDate, dueDate)

    aggregated_data = {
        'currency': currency,
        'subTotal': total_subTotal,
        'totalTaxAmount': total_taxAmount,
        'totalAmount': total_amount,
        'amountDue': total_amountDue,
        'totalCount': total_count,
        'earliestIssueDate': earliest_issueDate.isoformat(),
        'latestIssueDate': latest_issueDate.isoformat(),
        'earliestDueDate': earliest_dueDate.isoformat(),
        'latestDueDate': latest_dueDate.isoformat()
    }

    return json.dumps(aggregated_data)

def remove_nodes(json_string, node_names):
    before = len(json_string)
    for node_name in node_names:
        data = json.loads(json_string)
        for result in data['results']:
            if node_name in result:
                del result[node_name]
        json_string = json.dumps(data)
    after = len(json_string)
    print(f"MIN: from {before} to {after} with {node_names} removal")
    return json_string


@app.get("/codat.png")
async def plugin_logo():
    filename = 'codat.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)

if __name__ == "__main__":
    main()

