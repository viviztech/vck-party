# VCK Political Party Management - API Reference

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.vck.app/api/v1
```

## Authentication
All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 1. Authentication APIs

### 1.1 Phone OTP Login

#### Request OTP
```http
POST /auth/otp/request
Content-Type: application/json

{
    "phone": "+919876543210",
    "purpose": "login"  // "login" | "registration"
}
```

**Response:**
```json
{
    "success": true,
    "message": "OTP sent successfully",
    "data": {
        "expires_in": 300,
        "retry_after": 60
    }
}
```

#### Verify OTP
```http
POST /auth/otp/verify
Content-Type: application/json

{
    "phone": "+919876543210",
    "otp": "123456",
    "device_info": {
        "device_id": "abc123",
        "device_type": "android",
        "app_version": "1.0.0"
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "token_type": "Bearer",
        "expires_in": 900,
        "user": {
            "id": "uuid",
            "phone": "+919876543210",
            "is_member": true,
            "member_id": "uuid"
        }
    }
}
```

### 1.2 Email Login
```http
POST /auth/login/email
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

### 1.3 Social Login
```http
POST /auth/login/social
Content-Type: application/json

{
    "provider": "google",  // "google" | "facebook"
    "token": "oauth_token_from_provider"
}
```

### 1.4 Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJhbGc..."
}
```

### 1.5 Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>

{
    "refresh_token": "eyJhbGc..."
}
```

---

## 2. Member APIs

### 2.1 Register New Member
```http
POST /members/register
Content-Type: application/json

{
    "first_name": "Karthik",
    "last_name": "Kumar",
    "first_name_ta": "கார்த்திக்",
    "last_name_ta": "குமார்",
    "phone": "+919876543210",
    "email": "karthik@example.com",
    "date_of_birth": "1990-05-15",
    "gender": "male",
    "address_line1": "123 Main Street",
    "city": "Chennai",
    "district": "Chennai",
    "pincode": "600001",
    "voter_id": "ABC1234567",
    "occupation": "Engineer",
    "skills": ["social_media", "public_speaking"]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "member_id": "uuid",
        "membership_number": "VCK2024001234",
        "status": "pending",
        "message": "Registration submitted. Awaiting verification."
    }
}
```

### 2.2 Get Member Profile
```http
GET /members/{member_id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "membership_number": "VCK2024001234",
        "first_name": "Karthik",
        "last_name": "Kumar",
        "photo_url": "https://...",
        "phone": "+919876543210",
        "email": "karthik@example.com",
        "status": "active",
        "joined_at": "2024-01-15T10:30:00Z",
        "units": [
            {
                "unit_id": "uuid",
                "unit_name": "Chennai District",
                "unit_type": "district",
                "position": "Member",
                "is_primary": true
            }
        ],
        "engagement_score": 75,
        "badges": [
            {
                "id": "uuid",
                "name": "Active Volunteer",
                "icon_url": "https://...",
                "earned_at": "2024-06-01T00:00:00Z"
            }
        ]
    }
}
```

### 2.3 Update Member Profile
```http
PUT /members/{member_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "email": "new.email@example.com",
    "occupation": "Software Engineer",
    "skills": ["social_media", "public_speaking", "event_management"]
}
```

### 2.4 List Members
```http
GET /members?unit_id={unit_id}&status=active&page=1&limit=20&search=karthik
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| unit_id | uuid | Filter by organization unit |
| status | string | Filter by status (pending/active/suspended) |
| position_id | uuid | Filter by position |
| search | string | Search by name or phone |
| page | int | Page number (default: 1) |
| limit | int | Items per page (default: 20, max: 100) |

**Response:**
```json
{
    "success": true,
    "data": {
        "members": [...],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 150,
            "total_pages": 8
        }
    }
}
```

### 2.5 Transfer Member
```http
POST /members/{member_id}/transfer
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "to_unit_id": "uuid",
    "reason": "Relocated to new district"
}
```

### 2.6 Get Member Activities
```http
GET /members/{member_id}/activities?type=event_attendance&from=2024-01-01&to=2024-12-31
Authorization: Bearer <access_token>
```

---

## 3. Hierarchy APIs

### 3.1 Get Organization Tree
```http
GET /hierarchy/units?type=state&include_children=true&depth=2
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "units": [
            {
                "id": "uuid",
                "name": "Tamil Nadu",
                "code": "TN",
                "type": "state",
                "member_count": 50000,
                "children": [
                    {
                        "id": "uuid",
                        "name": "Chennai",
                        "code": "TN.CHN",
                        "type": "district",
                        "member_count": 10000,
                        "children": [...]
                    }
                ]
            }
        ]
    }
}
```

### 3.2 Get Unit Details
```http
GET /hierarchy/units/{unit_id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "name": "Chennai District",
        "code": "TN.CHN",
        "type": "district",
        "path": "TN.CHN",
        "parent": {
            "id": "uuid",
            "name": "Tamil Nadu",
            "type": "state"
        },
        "statistics": {
            "total_members": 10000,
            "active_members": 8500,
            "events_this_month": 15,
            "avg_engagement": 68
        },
        "office_bearers": [
            {
                "position": "District President",
                "member": {
                    "id": "uuid",
                    "name": "Name",
                    "photo_url": "https://..."
                }
            }
        ]
    }
}
```

### 3.3 Create Unit
```http
POST /hierarchy/units
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Velachery Booth 101",
    "code": "TN.CHN.VEL.101",
    "type": "booth",
    "parent_id": "uuid",
    "geo_boundary": {
        "type": "Polygon",
        "coordinates": [[[...], [...], ...]]
    }
}
```

### 3.4 Assign Position
```http
POST /hierarchy/units/{unit_id}/positions
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "member_id": "uuid",
    "position_id": "uuid",
    "effective_from": "2024-01-01"
}
```

### 3.5 Get Unit Members
```http
GET /hierarchy/units/{unit_id}/members?include_sub_units=true&page=1&limit=50
Authorization: Bearer <access_token>
```

---

## 4. Events APIs

### 4.1 Create Event
```http
POST /events
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "District General Meeting",
    "title_ta": "மாவட்ட பொதுக்கூட்டம்",
    "description": "Monthly meeting of all district members",
    "type": "meeting",
    "unit_id": "uuid",
    "start_time": "2024-03-15T18:00:00+05:30",
    "end_time": "2024-03-15T20:00:00+05:30",
    "venue_name": "Party Office Hall",
    "venue_address": "123 Anna Salai, Chennai",
    "geo_location": {
        "type": "Point",
        "coordinates": [80.2707, 13.0827]
    },
    "max_attendees": 200,
    "registration_required": true,
    "registration_deadline": "2024-03-14T23:59:59+05:30"
}
```

### 4.2 Get Events
```http
GET /events?unit_id={uuid}&type=rally&status=published&from=2024-03-01&to=2024-03-31
Authorization: Bearer <access_token>
```

### 4.3 Get Event Details
```http
GET /events/{event_id}
Authorization: Bearer <access_token>
```

### 4.4 Register for Event
```http
POST /events/{event_id}/register
Authorization: Bearer <access_token>
```

### 4.5 Check-in to Event
```http
POST /events/{event_id}/check-in
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "location": {
        "type": "Point",
        "coordinates": [80.2707, 13.0827]
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "status": "attended",
        "check_in_time": "2024-03-15T18:05:00+05:30",
        "points_earned": 10
    }
}
```

### 4.6 Get Event Analytics
```http
GET /events/{event_id}/analytics
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "registrations": 180,
        "attended": 165,
        "attendance_rate": 91.7,
        "by_unit": [
            {"unit": "Booth 101", "count": 25},
            {"unit": "Booth 102", "count": 30}
        ],
        "check_in_timeline": [
            {"time": "18:00", "count": 50},
            {"time": "18:15", "count": 80}
        ]
    }
}
```

---

## 5. Campaign APIs

### 5.1 Create Campaign
```http
POST /campaigns
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Door-to-Door Voter Outreach",
    "description": "Connect with voters before elections",
    "unit_id": "uuid",
    "start_date": "2024-04-01",
    "end_date": "2024-04-30",
    "goals": {
        "target_voters": 10000,
        "door_visits": 5000,
        "new_members": 100
    },
    "budget": 50000.00
}
```

### 5.2 Get Campaign Progress
```http
GET /campaigns/{campaign_id}/progress
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "campaign_id": "uuid",
        "goals": {
            "target_voters": {"target": 10000, "achieved": 6500, "percentage": 65},
            "door_visits": {"target": 5000, "achieved": 3200, "percentage": 64},
            "new_members": {"target": 100, "achieved": 45, "percentage": 45}
        },
        "tasks": {
            "total": 50,
            "completed": 32,
            "in_progress": 10,
            "pending": 8
        },
        "top_volunteers": [...]
    }
}
```

### 5.3 Create Campaign Task
```http
POST /campaigns/{campaign_id}/tasks
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Visit Booth 101 voters",
    "description": "Complete door visits for assigned area",
    "assigned_to": "uuid",
    "unit_id": "uuid",
    "due_date": "2024-04-15T18:00:00+05:30",
    "priority": 1
}
```

---

## 6. Communication APIs

### 6.1 Create Announcement
```http
POST /communications/announcements
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "Important Notice",
    "title_ta": "முக்கிய அறிவிப்பு",
    "content": "All members are requested to attend...",
    "content_ta": "அனைத்து உறுப்பினர்களும்...",
    "unit_id": "uuid",
    "target_scope": "district",
    "send_push": true,
    "send_sms": false,
    "publish_at": "2024-03-10T09:00:00+05:30",
    "image_url": "https://..."
}
```

### 6.2 Get Announcements
```http
GET /communications/announcements?unit_id={uuid}&pinned=true
Authorization: Bearer <access_token>
```

### 6.3 Create Discussion
```http
POST /communications/discussions
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "unit_id": "uuid",
    "title": "Ideas for upcoming rally",
    "content": "Let's discuss creative ideas..."
}
```

### 6.4 Submit Grievance
```http
POST /communications/grievances
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "unit_id": "uuid",
    "category": "local_issue",
    "subject": "Road repair needed",
    "description": "The main road in our area has potholes...",
    "attachments": ["https://..."]
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "grievance_id": "uuid",
        "ticket_number": "GRV2024001234",
        "status": "submitted",
        "message": "Your grievance has been registered."
    }
}
```

---

## 7. Analytics APIs (Data Science)

### 7.1 Voter Demographics
```http
GET /analytics/voter/demographics?unit_id={uuid}&group_by=age,gender
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_voters": 125000,
        "by_age": [
            {"group": "18-25", "count": 25000, "percentage": 20},
            {"group": "26-35", "count": 35000, "percentage": 28},
            {"group": "36-50", "count": 40000, "percentage": 32},
            {"group": "50+", "count": 25000, "percentage": 20}
        ],
        "by_gender": [
            {"group": "male", "count": 62000, "percentage": 49.6},
            {"group": "female", "count": 63000, "percentage": 50.4}
        ]
    }
}
```

### 7.2 Election Predictions
```http
GET /analytics/voter/predictions?election_id={uuid}&unit_type=booth
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "election_id": "uuid",
        "overall_prediction": {
            "win_probability": 0.72,
            "expected_vote_share": 45.5,
            "margin": 12000,
            "confidence": 0.85
        },
        "by_unit": [
            {
                "unit_id": "uuid",
                "unit_name": "Booth 101",
                "prediction": {
                    "total_voters": 1200,
                    "expected_votes": 580,
                    "win_probability": 0.78
                }
            }
        ],
        "model_info": {
            "version": "v2.1",
            "last_trained": "2024-03-01",
            "accuracy": 0.82
        }
    }
}
```

### 7.3 Current Sentiment
```http
GET /analytics/sentiment/current?region=chennai&topic=party_name
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "timestamp": "2024-03-10T12:00:00Z",
        "overall_sentiment": 0.35,
        "sentiment_label": "positive",
        "volume": 1250,
        "distribution": {
            "positive": 55,
            "neutral": 30,
            "negative": 15
        },
        "trending_topics": [
            {"topic": "rally", "sentiment": 0.65, "volume": 320},
            {"topic": "policy", "sentiment": 0.42, "volume": 180}
        ],
        "top_positive_posts": [...],
        "top_negative_posts": [...]
    }
}
```

### 7.4 Sentiment Trends
```http
GET /analytics/sentiment/trends?from=2024-01-01&to=2024-03-10&granularity=daily
Authorization: Bearer <access_token>
```

### 7.5 Member Engagement Scores
```http
GET /analytics/engagement/scores?unit_id={uuid}&sort=score&order=desc&limit=100
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "unit_average": 62,
        "members": [
            {
                "member_id": "uuid",
                "name": "Karthik Kumar",
                "score": 95,
                "components": {
                    "event_participation": 30,
                    "donations": 20,
                    "campaign_tasks": 25,
                    "app_activity": 20
                },
                "badges_count": 5,
                "last_activity": "2024-03-09T15:30:00Z"
            }
        ]
    }
}
```

### 7.6 At-Risk Members (Churn Prediction)
```http
GET /analytics/engagement/at-risk?unit_id={uuid}&threshold=0.7
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "data": {
        "total_at_risk": 45,
        "members": [
            {
                "member_id": "uuid",
                "name": "Name",
                "churn_probability": 0.85,
                "risk_factors": [
                    "No activity in 60 days",
                    "Missed last 3 events",
                    "Low engagement score"
                ],
                "recommended_actions": [
                    "Personal outreach call",
                    "Invite to upcoming local event"
                ],
                "last_activity": "2024-01-15T10:00:00Z"
            }
        ]
    }
}
```

---

## 8. Voting APIs (eVoting)

### 8.1 Create Election
```http
POST /voting/elections
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "title": "District President Election 2024",
    "description": "Election for the position of District President",
    "unit_id": "uuid",
    "position_id": "uuid",
    "nominations_start": "2024-04-01T00:00:00+05:30",
    "nominations_end": "2024-04-07T23:59:59+05:30",
    "voting_start": "2024-04-10T08:00:00+05:30",
    "voting_end": "2024-04-10T20:00:00+05:30",
    "eligible_voter_criteria": {
        "min_membership_months": 6,
        "status": ["active"],
        "positions": []
    }
}
```

### 8.2 Get Elections
```http
GET /voting/elections?unit_id={uuid}&status=voting_open
Authorization: Bearer <access_token>
```

### 8.3 Get Election Details
```http
GET /voting/elections/{election_id}
Authorization: Bearer <access_token>
```

### 8.4 Nominate Candidate
```http
POST /voting/elections/{election_id}/nominate
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "member_id": "uuid",
    "manifesto": "My vision for the district..."
}
```

### 8.5 Cast Vote
```http
POST /voting/elections/{election_id}/vote
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "candidate_id": "uuid"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "vote_receipt": "VR2024001234",
        "message": "Your vote has been recorded successfully."
    }
}
```

### 8.6 Get Election Results
```http
GET /voting/elections/{election_id}/results
Authorization: Bearer <access_token>
```

---

## 9. Donation APIs

### 9.1 Create Donation
```http
POST /donations
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "campaign_id": "uuid",
    "amount": 1000.00,
    "payment_method": "upi"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "donation_id": "uuid",
        "payment_order_id": "order_abc123",
        "amount": 1000.00,
        "payment_link": "https://razorpay.com/...",
        "qr_code": "data:image/png;base64,..."
    }
}
```

### 9.2 Verify Payment
```http
POST /donations/{donation_id}/verify
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "payment_id": "pay_abc123",
    "signature": "..."
}
```

### 9.3 Get Donation History
```http
GET /donations?member_id={uuid}&from=2024-01-01&to=2024-12-31
Authorization: Bearer <access_token>
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid phone number format",
        "details": {
            "field": "phone",
            "reason": "Must be a valid Indian phone number"
        }
    }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| UNAUTHORIZED | 401 | Missing or invalid token |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

---

## Rate Limits

| Endpoint Category | Limit |
|------------------|-------|
| Authentication | 10 requests/minute |
| General APIs | 100 requests/minute |
| Analytics | 20 requests/minute |
| File Upload | 10 requests/minute |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710072000
```
