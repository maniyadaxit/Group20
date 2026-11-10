# Network Analysis

## Website Tested

https://example.com/

## Procedure

1. Opened the website in Google Chrome.
2. Opened Chrome DevTools.
3. Selected the Network tab.
4. Enabled the **Disable cache** option.
5. Reloaded the page.
6. Observed the requests and Network waterfall.

## Results

### Request Count

**Total requests:** 1

### Total Page Size

**Total page resources:** 559 B

**Data transferred:** 400 B

### Slowest Resource

**Resource:** `/?utm_source=chatgpt.com`

**Time:** 1.50 s

### 3xx / 4xx Responses

No 3xx or 4xx responses were observed during this reload. The only request returned a `200 OK` status.

## Conclusion

The Network panel showed that the page was loaded using one HTTP request. With cache disabled, the browser transferred 400 B and loaded 559 B of total resources. The single document request was also the slowest resource, taking 1.50 seconds.
