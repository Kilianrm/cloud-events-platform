## 2026-03-21 – Rate Limiting & Traffic Control for Internal Clients

**Decision**  
Use **API Gateway native rate limiting and throttling** combined with per-service quotas to protect ingestion and read APIs from abuse or accidental overuse. Each service request is subject to a maximum request rate and burst capacity, enforced by API Gateway. Lambda input validation complements this to ensure robust protection.

**Reasoning**  
- API Gateway provides **native, per-client rate limiting and throttling** without additional custom logic.  
- Maintaining quotas and limits at the gateway level **reduces load on Lambdas** and downstream DynamoDB.  
- Complements JWT-based authentication, allowing **per-service traffic control**.  
- Provides standard error responses (`429 Too Many Requests`) to indicate throttling to clients.

**Alternatives Considered**  
1. **Custom throttling in Lambda**  
   - Pros: Full control, can implement complex policies.  
   - Cons: Adds load and complexity to Lambda functions; less efficient than gateway-level throttling.  

2. **API Key based throttling**  
   - Pros: Easy to implement with API Gateway.  
   - Cons: API Keys alone do not provide verifiable service identity or fine-grained access control; security is weaker.  

3. **No throttling**  
   - Pros: Simplest setup.  
   - Cons: High risk of abuse, accidental overuse, and degraded performance.  

**Decision Outcome**  
Using **API Gateway native rate limiting and throttling**, together with JWT authentication, provides the **best combination of security, simplicity, and reliability** for controlling access and traffic per internal client.