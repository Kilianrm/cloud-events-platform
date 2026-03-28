"## 2026-03-21 – Authentication Choice for Internal Clients

### **Decision**  
The system implements **JWT-based authentication** for internal clients. Each client (service) has:

- `client_id`  
- `secret`

Authentication flow:

1. The client requests a JWT from the internal Auth Service using `client_id` and `secret`.  
2. The Auth Service issues a signed JWT and returns it to the client.  
3. The client includes the JWT in API requests: 
Authorization: Bearer <jwt>
4. API Gateway (HTTP API v2) uses a **JWT Authorizer** to validate the token before invoking the corresponding Lambda function.

---

### **Reasoning**  

- The goal was to implement a **professional and scalable solution** suitable for a portfolio project.  
- The architecture separates **authentication** from **business logic**.  
- JWT allows embedding **claims** in the payload, making future evolution easier (roles, scopes, expiration).  
- Fully compatible with HTTP API v2 using a Lambda Authorizer.  
- Even though clients are internal, this simulates a real identity system and demonstrates good security practices.

---

### **Alternatives Considered**  

#### 1. HMAC per request
- ✔ Very simple and secure for individual requests.  
- ❌ Less “impressive” for portfolio and less extensible for future iterations.  

#### 2. API Keys (API Gateway)
- ❌ Not compatible with HTTP API v2  
- ❌ Limited security (does not protect payload or support claims)  

#### 3. Amazon Cognito
- ✔ Managed and secure  
- ❌ Designed for human users  
- ❌ Overkill for internal service clients  

#### 4. IAM Authentication (Signature V4)
- ✔ Very secure  
- ❌ High complexity and overengineering for an internal system  

---

### **Decision Outcome**  

- ✔ JWT-based authentication is implemented internally, aligning with the portfolio vision.  
- ✔ Supports future evolution with roles, scopes, or multi-API setups.  
- ✔ Maintains security and control over internal service clients.  

Trade-offs accepted:
- Requires an **Auth Service** to issue JWTs and validation logic in Lambda.  
- Higher initial complexity compared to HMAC, but demonstrates real-world architecture and best practices."

"## JWT Authentication Flow – Internal Clients
