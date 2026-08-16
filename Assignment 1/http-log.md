# HTTP Request and Response Log

## Request 1 — Get Post 1

### Command

```bash
curl -i https://jsonplaceholder.typicode.com/posts/1
```

### Full Response

```text
HTTP/2 200
date: Sun, 16 Aug 2026 09:32:09 GMT
content-type: application/json; charset=utf-8
content-length: 292
access-control-allow-credentials: true
cache-control: max-age=43200
etag: W/"124-yiKdLzqO5gfBrJFrcdJ8Yq0LGnU"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
report-to: {"group":"heroku-nel","endpoints":[{"url":"https://nel.heroku.com/reports?s=PD3aZ5JXmnXLLbuM9yuy2jwg6ke8U5C2Yq%2BT0erzkj0%3D\u0026sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d\u0026ts=1775729378"}],"max_age":3600}
reporting-endpoints: heroku-nel="https://nel.heroku.com/reports?s=PD3aZ5JXmnXLLbuM9yuy2jwg6ke8U5C2Yq%2BT0erzkj0%3D&sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d&ts=1775729378"
server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 730
x-ratelimit-reset: 1775729393
age: 4011
accept-ranges: bytes
cf-cache-status: HIT
cf-ray: a2bf6e21e9d9ce7e-SIN
alt-svc: h3=":443"; ma=86400

{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
}
```

### Notes

- **Status code — 200 OK:** The server successfully processed the request and returned the requested resource.
- **Content-Type — application/json; charset=utf-8:** The response body contains data in JSON format, encoded using UTF-8.

## Request 2 — Get Post 2

### Command

```bash
curl -i https://jsonplaceholder.typicode.com/posts/2
```

### Full Response

```text
HTTP/2 200
date: Sun, 16 Aug 2026 09:36:10 GMT
content-type: application/json; charset=utf-8
content-length: 278
access-control-allow-credentials: true
cache-control: max-age=43200
etag: W/"116-jnDuMpjju89+9j7e0BqkdFsVRjs"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
report-to: {"group":"heroku-nel","endpoints":[{"url":"https://nel.heroku.com/reports?s=agjb5%2BTOo7JOqqHsLS%2BkIRCu1NXxnFiFIEaByoR9r3I%3D\u0026sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d\u0026ts=1786868122"}],"max_age":3600}
reporting-endpoints: heroku-nel="https://nel.heroku.com/reports?s=agjb5%2BTOo7JOqqHsLS%2BkIRCu1NXxnFiFIEaByoR9r3I%3D&sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d&ts=1786868122"
server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 999
x-ratelimit-reset: 1786868142
age: 4847
accept-ranges: bytes
cf-cache-status: HIT
cf-ray: a2bf73ff9dc3a146-SIN
alt-svc: h3=":443"; ma=86400

{
  "userId": 1,
  "id": 2,
  "title": "qui est esse",
  "body": "est rerum tempore vitae\nsequi sint nihil reprehenderit dolor beatae ea dolores neque\nfugiat blanditiis voluptate porro vel nihil molestiae ut reiciendis\nqui aperiam non debitis possimus qui neque nisi nulla"
}
```

### Notes

- **Status code — 200 OK:** The request was successful, and the server returned Post 2.
- **Content-Type — application/json; charset=utf-8:** The response body is JSON data encoded using UTF-8.

## Request 3 — Get User 1

### Command

```bash
curl -i https://jsonplaceholder.typicode.com/users/1
```

### Full Response

```text
HTTP/2 200
date: Sun, 16 Aug 2026 09:37:17 GMT
content-type: application/json; charset=utf-8
content-length: 509
access-control-allow-credentials: true
cache-control: max-age=43200
etag: W/"1fd-+2Y3G3w049iSZtw5t1mzSnunngE"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
report-to: {"group":"heroku-nel","endpoints":[{"url":"https://nel.heroku.com/reports?s=hcim2HEuPeWVzmNQK6NPKzhenGdnMXEOagm00OjdjcU%3D\u0026sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d\u0026ts=1786848777"}],"max_age":3600}
reporting-endpoints: heroku-nel="https://nel.heroku.com/reports?s=hcim2HEuPeWVzmNQK6NPKzhenGdnMXEOagm00OjdjcU%3D&sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d&ts=1786848777"
server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 997
x-ratelimit-reset: 1786848823
age: 24259
accept-ranges: bytes
cf-cache-status: HIT
cf-ray: a2bf75a1fd26f882-SIN
alt-svc: h3=":443"; ma=86400

{
  "id": 1,
  "name": "Leanne Graham",
  "username": "Bret",
  "email": "Sincere@april.biz",
  "address": {
    "street": "Kulas Light",
    "suite": "Apt. 556",
    "city": "Gwenborough",
    "zipcode": "92998-3874",
    "geo": {
      "lat": "-37.3159",
      "lng": "81.1496"
    }
  },
  "phone": "1-770-736-8031 x56442",
  "website": "hildegard.org",
  "company": {
    "name": "Romaguera-Crona",
    "catchPhrase": "Multi-layered client-server neural-net",
    "bs": "harness real-time e-markets"
  }
}
```

### Notes

* **Status code — 200 OK:** The request was successfully processed, and the server returned the requested user resource.
* **Content-Type — application/json; charset=utf-8:** The response body contains JSON data encoded using UTF-8.

## Request 4 — Get Comment 1

### Command

```bash
curl -i https://jsonplaceholder.typicode.com/comments/1
```

### Full Response

```text
HTTP/2 200
date: Sun, 16 Aug 2026 09:38:54 GMT
content-type: application/json; charset=utf-8
content-length: 268
access-control-allow-credentials: true
cache-control: max-age=43200
etag: W/"10c-KJ4I9RM/+33TKdV8CFsIvqsDSP0"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
report-to: {"group":"heroku-nel","endpoints":[{"url":"https://nel.heroku.com/reports?s=juUFUla4sclQXiOziFb%2B7LWRR7Hh%2BVY8G8E%2Bpbnmoo8%3D\u0026sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d\u0026ts=1786868245"}],"max_age":3600}
reporting-endpoints: heroku-nel="https://nel.heroku.com/reports?s=juUFUla4sclQXiOziFb%2B7LWRR7Hh%2BVY8G8E%2Bpbnmoo8%3D&sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d&ts=1786868245"
server: cloudflare
vary: Origin
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 996
x-ratelimit-reset: 1786868262
age: 4889
accept-ranges: bytes
cf-cache-status: HIT
cf-ray: a2bf7803ab34a8e7-SIN
alt-svc: h3=":443"

{
  "postId": 1,
  "id": 1,
  "name": "id labore ex et quam laborum",
  "email": "Eliseo@gardner.biz",
  "body": "laudantium enim quasi est quidem magnam voluptate ipsam eos\ntempora quo necessitatibus\ndolor quam autem quasi\nreiciendis et nam sapiente accusantium"
}
```

### Notes

* **Status code — 200 OK:** The request was successfully processed and the requested comment was returned.
* **Content-Type — application/json; charset=utf-8:** The response body contains JSON data encoded using UTF-8.

## Request 5 — Request a Non-Existent Post

### Command

```bash
curl -i https://jsonplaceholder.typicode.com/posts/999999
```

### Full Response

```text
HTTP/2 404
date: Sun, 16 Aug 2026 09:40:07 GMT
content-type: application/json; charset=utf-8
content-length: 2
access-control-allow-credentials: true
cache-control: max-age=43200
etag: W/"2-vyGp6PvFo4RvsFtPoIWeCReyIC8"
expires: -1
nel: {"report_to":"heroku-nel","response_headers":["Via"],"max_age":3600,"success_fraction":0.01,"failure_fraction":0.1}
pragma: no-cache
report-to: {"group":"heroku-nel","endpoints":[{"url":"https://nel.heroku.com/reports?s=O9TMQru8qx%2Fazpa07AHu3WTGxsl9dx9fZVsfS0y9fLs%3D\u0026sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d\u0026ts=1786866447"}],"max_age":3600}
reporting-endpoints: heroku-nel="https://nel.heroku.com/reports?s=O9TMQru8qx%2Fazpa07AHu3WTGxsl9dx9fZVsfS0y9fLs%3D&sid=e11707d5-02a7-43ef-b45e-2cf4d2036f7d&ts=1786866447"
server: cloudflare
vary: Origin, Accept-Encoding
via: 2.0 heroku-router
x-content-type-options: nosniff
x-powered-by: Express
x-ratelimit-limit: 1000
x-ratelimit-remaining: 998
x-ratelimit-reset: 1786866462
age: 6759
cf-cache-status: HIT
cf-ray: a2bf79ccffff5941-SIN
alt-svc: h3=":443"; ma=86400

{}
```

### Notes

* **Status code — 404 Not Found:** The server could not find the requested resource because Post `999999` does not exist.
* **Content-Type — application/json; charset=utf-8:** The server returned the response body in JSON format, encoded using UTF-8. In this case, the JSON body is an empty object: `{}`.
