# VCK Political Party Management - Database Schema

## PostgreSQL Schema (Primary Database)

### 1. Authentication & Users

```sql
-- Users table (for authentication)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OTP verification
CREATE TABLE otp_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(15) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    purpose VARCHAR(50) NOT NULL, -- 'login', 'registration', 'reset'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Social login connections
CREATE TABLE social_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'google', 'facebook'
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_user_id)
);

-- Refresh tokens
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    device_info JSONB,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Organization Hierarchy

```sql
-- Enable ltree extension for hierarchical queries
CREATE EXTENSION IF NOT EXISTS ltree;
CREATE EXTENSION IF NOT EXISTS postgis;

-- Organization unit types
CREATE TYPE unit_type AS ENUM ('state', 'district', 'constituency', 'booth', 'ward');

-- Organization units (party structure)
CREATE TABLE organization_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'TN', 'TN.CHN', 'TN.CHN.001'
    type unit_type NOT NULL,
    path ltree NOT NULL, -- hierarchical path for efficient queries
    parent_id UUID REFERENCES organization_units(id),
    geo_boundary GEOMETRY(POLYGON, 4326), -- PostGIS boundary
    center_point GEOMETRY(POINT, 4326),
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for hierarchy queries
CREATE INDEX idx_org_units_path ON organization_units USING GIST (path);
CREATE INDEX idx_org_units_parent ON organization_units(parent_id);
CREATE INDEX idx_org_units_geo ON organization_units USING GIST (geo_boundary);

-- Positions/Roles within units
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_ta VARCHAR(100), -- Tamil translation
    level INTEGER NOT NULL, -- 1=highest (President), 10=lowest
    unit_type unit_type NOT NULL,
    permissions JSONB DEFAULT '[]',
    is_elected BOOLEAN DEFAULT false,
    max_holders INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Members

```sql
-- Member status
CREATE TYPE member_status AS ENUM ('pending', 'active', 'suspended', 'expelled', 'resigned');

-- Members table
CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    membership_number VARCHAR(50) UNIQUE,

    -- Personal information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    first_name_ta VARCHAR(100), -- Tamil name
    last_name_ta VARCHAR(100),
    photo_url TEXT,
    date_of_birth DATE,
    gender VARCHAR(20),

    -- Contact
    phone VARCHAR(15) NOT NULL,
    alternate_phone VARCHAR(15),
    email VARCHAR(255),

    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    district VARCHAR(100),
    state VARCHAR(100) DEFAULT 'Tamil Nadu',
    pincode VARCHAR(10),
    geo_location GEOMETRY(POINT, 4326),

    -- Political info
    voter_id VARCHAR(50),
    aadhar_hash VARCHAR(255), -- hashed for privacy
    blood_group VARCHAR(5),
    education VARCHAR(100),
    occupation VARCHAR(100),
    skills TEXT[],

    -- Membership details
    status member_status DEFAULT 'pending',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES members(id),

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_members_phone ON members(phone);
CREATE INDEX idx_members_status ON members(status);
CREATE INDEX idx_members_geo ON members USING GIST (geo_location);
CREATE INDEX idx_members_voter_id ON members(voter_id);

-- Member-Unit relationships (a member can belong to multiple units)
CREATE TABLE member_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    unit_id UUID REFERENCES organization_units(id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id),
    is_primary BOOLEAN DEFAULT false,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    appointed_by UUID REFERENCES members(id),
    notes TEXT,
    UNIQUE(member_id, unit_id, position_id)
);

-- Member transfers history
CREATE TABLE member_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    from_unit_id UUID REFERENCES organization_units(id),
    to_unit_id UUID REFERENCES organization_units(id),
    reason TEXT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by UUID REFERENCES members(id),
    status VARCHAR(20) DEFAULT 'pending' -- pending, approved, rejected
);
```

### 4. Events & Campaigns

```sql
-- Event types
CREATE TYPE event_type AS ENUM ('rally', 'meeting', 'protest', 'campaign', 'training', 'celebration', 'other');
CREATE TYPE event_status AS ENUM ('draft', 'published', 'ongoing', 'completed', 'cancelled');

-- Events
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    title_ta VARCHAR(255),
    description TEXT,
    description_ta TEXT,
    type event_type NOT NULL,

    -- Organization
    unit_id UUID REFERENCES organization_units(id),
    created_by UUID REFERENCES members(id),

    -- Schedule
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,

    -- Location
    venue_name VARCHAR(255),
    venue_address TEXT,
    geo_location GEOMETRY(POINT, 4326),
    geo_fence_radius INTEGER DEFAULT 100, -- meters for check-in

    -- Capacity
    max_attendees INTEGER,
    registration_required BOOLEAN DEFAULT false,
    registration_deadline TIMESTAMP WITH TIME ZONE,

    -- Media
    banner_url TEXT,
    media_urls TEXT[],

    -- Status
    status event_status DEFAULT 'draft',

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event attendees
CREATE TYPE attendance_status AS ENUM ('registered', 'confirmed', 'attended', 'no_show', 'cancelled');

CREATE TABLE event_attendees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    status attendance_status DEFAULT 'registered',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_in_location GEOMETRY(POINT, 4326),
    check_out_time TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    UNIQUE(event_id, member_id)
);

-- Campaigns
CREATE TYPE campaign_status AS ENUM ('planning', 'active', 'paused', 'completed', 'cancelled');

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    name_ta VARCHAR(255),
    description TEXT,
    description_ta TEXT,

    unit_id UUID REFERENCES organization_units(id),
    created_by UUID REFERENCES members(id),

    start_date DATE NOT NULL,
    end_date DATE,

    goals JSONB DEFAULT '{}', -- {target_voters: 10000, door_visits: 5000, etc.}
    budget DECIMAL(12, 2),

    status campaign_status DEFAULT 'planning',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campaign tasks
CREATE TABLE campaign_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES members(id),
    unit_id UUID REFERENCES organization_units(id),
    due_date TIMESTAMP WITH TIME ZONE,
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. Communications

```sql
-- Announcements
CREATE TYPE announcement_scope AS ENUM ('all', 'state', 'district', 'constituency', 'booth');

CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    title_ta VARCHAR(255),
    content TEXT NOT NULL,
    content_ta TEXT,

    created_by UUID REFERENCES members(id),
    unit_id UUID REFERENCES organization_units(id),
    target_scope announcement_scope DEFAULT 'all',

    -- Delivery channels
    send_push BOOLEAN DEFAULT true,
    send_sms BOOLEAN DEFAULT false,
    send_email BOOLEAN DEFAULT false,

    -- Schedule
    publish_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Media
    image_url TEXT,
    attachment_urls TEXT[],

    is_pinned BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Discussions/Forums
CREATE TABLE discussions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_id UUID REFERENCES organization_units(id),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id UUID REFERENCES members(id),

    is_pinned BOOLEAN DEFAULT false,
    is_locked BOOLEAN DEFAULT false,

    views_count INTEGER DEFAULT 0,
    replies_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Discussion replies
CREATE TABLE discussion_replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    discussion_id UUID REFERENCES discussions(id) ON DELETE CASCADE,
    parent_reply_id UUID REFERENCES discussion_replies(id),
    author_id UUID REFERENCES members(id),
    content TEXT NOT NULL,

    is_approved BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Grievances
CREATE TYPE grievance_status AS ENUM ('submitted', 'acknowledged', 'in_progress', 'resolved', 'closed', 'rejected');
CREATE TYPE grievance_priority AS ENUM ('low', 'medium', 'high', 'urgent');

CREATE TABLE grievances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number VARCHAR(20) UNIQUE NOT NULL,

    member_id UUID REFERENCES members(id),
    unit_id UUID REFERENCES organization_units(id),

    category VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    priority grievance_priority DEFAULT 'medium',
    status grievance_status DEFAULT 'submitted',

    assigned_to UUID REFERENCES members(id),

    attachments TEXT[],

    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. Engagement & Gamification

```sql
-- Member activities (for engagement scoring)
CREATE TABLE member_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL, -- 'event_attendance', 'donation', 'campaign_task', etc.
    activity_id UUID, -- reference to the activity
    points INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_member_activities_member ON member_activities(member_id);
CREATE INDEX idx_member_activities_type ON member_activities(activity_type);

-- Engagement scores (computed periodically)
CREATE TABLE engagement_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id) ON DELETE CASCADE UNIQUE,
    score INTEGER DEFAULT 0, -- 0-100
    components JSONB DEFAULT '{}', -- breakdown of score
    churn_probability DECIMAL(5, 4), -- 0.0000 to 1.0000
    last_activity_at TIMESTAMP WITH TIME ZONE,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Badges
CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_ta VARCHAR(100),
    description TEXT,
    description_ta TEXT,
    icon_url TEXT,
    criteria JSONB NOT NULL, -- conditions to earn
    points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Member badges
CREATE TABLE member_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    badge_id UUID REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(member_id, badge_id)
);
```

### 7. Donations & Finance

```sql
-- Donation campaigns
CREATE TABLE donation_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_id UUID REFERENCES organization_units(id),

    target_amount DECIMAL(12, 2),
    collected_amount DECIMAL(12, 2) DEFAULT 0,

    start_date DATE NOT NULL,
    end_date DATE,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Donations
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');

CREATE TABLE donations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES donation_campaigns(id),
    member_id UUID REFERENCES members(id),

    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',

    -- Payment details
    payment_method VARCHAR(50), -- 'upi', 'card', 'netbanking', 'cash'
    payment_gateway VARCHAR(50), -- 'razorpay', 'stripe'
    transaction_id VARCHAR(255),
    payment_status payment_status DEFAULT 'pending',

    -- Donor info (for non-member donations)
    donor_name VARCHAR(255),
    donor_phone VARCHAR(15),
    donor_email VARCHAR(255),
    donor_pan VARCHAR(20), -- for tax receipts

    receipt_number VARCHAR(50),
    receipt_url TEXT,

    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### 8. eVoting

```sql
-- Elections
CREATE TYPE election_status AS ENUM ('draft', 'nominations_open', 'voting_open', 'closed', 'results_declared');

CREATE TABLE elections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,

    unit_id UUID REFERENCES organization_units(id),
    position_id UUID REFERENCES positions(id), -- position being elected

    nominations_start TIMESTAMP WITH TIME ZONE,
    nominations_end TIMESTAMP WITH TIME ZONE,
    voting_start TIMESTAMP WITH TIME ZONE NOT NULL,
    voting_end TIMESTAMP WITH TIME ZONE NOT NULL,

    eligible_voter_criteria JSONB DEFAULT '{}',

    status election_status DEFAULT 'draft',

    created_by UUID REFERENCES members(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Candidates
CREATE TABLE election_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id),

    manifesto TEXT,
    photo_url TEXT,

    nominated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved BOOLEAN DEFAULT false,
    approved_by UUID REFERENCES members(id),

    votes_count INTEGER DEFAULT 0, -- updated after results

    UNIQUE(election_id, member_id)
);

-- Votes (anonymous, only tracks who voted, not whom)
CREATE TABLE election_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES election_candidates(id) ON DELETE CASCADE,

    -- Vote hash for verification without revealing voter
    vote_hash VARCHAR(255) NOT NULL,

    voted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Voter registry (tracks who has voted, not whom they voted for)
CREATE TABLE election_voters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
    member_id UUID REFERENCES members(id) ON DELETE CASCADE,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(election_id, member_id)
);
```

---

## MongoDB Schema (Analytics Database)

### 1. Voter Analytics Collections

```javascript
// voter_profiles - Voter data for analytics
{
    _id: ObjectId,
    voter_id: String,           // Electoral roll ID
    name: String,
    age: Number,
    gender: String,
    address: {
        booth_number: String,
        constituency: String,
        district: String
    },
    demographics: {
        education: String,
        occupation: String,
        income_bracket: String,
        religion: String,
        caste_category: String
    },
    voting_history: [{
        election_id: String,
        election_type: String,  // 'general', 'state', 'local'
        year: Number,
        voted: Boolean
    }],
    predicted_affinity: {
        party_score: Number,    // 0-100 likelihood to vote for party
        confidence: Number,
        factors: Object
    },
    last_contact: Date,
    contact_history: [{
        date: Date,
        type: String,           // 'door_visit', 'phone', 'event'
        notes: String,
        contacted_by: String
    }],
    tags: [String],
    created_at: Date,
    updated_at: Date
}

// election_predictions
{
    _id: ObjectId,
    election_id: String,
    election_type: String,
    election_date: Date,
    unit_id: String,            // booth/constituency
    unit_type: String,
    predictions: {
        total_voters: Number,
        expected_turnout: Number,
        party_votes: Number,
        win_probability: Number,
        margin: Number
    },
    model_info: {
        model_name: String,
        model_version: String,
        features_used: [String],
        accuracy_score: Number
    },
    created_at: Date
}
```

### 2. Sentiment Analysis Collections

```javascript
// social_posts - Collected social media data
{
    _id: ObjectId,
    source: String,             // 'twitter', 'facebook', 'news'
    post_id: String,
    author: {
        id: String,
        name: String,
        followers: Number
    },
    content: String,
    language: String,           // 'en', 'ta', 'hi'
    translated_content: String,

    analysis: {
        sentiment_score: Number,    // -1 to 1
        sentiment_label: String,    // 'positive', 'negative', 'neutral'
        topics: [String],
        entities: [{
            name: String,
            type: String,           // 'person', 'party', 'issue'
            sentiment: Number
        }],
        emotions: {
            joy: Number,
            anger: Number,
            fear: Number,
            surprise: Number
        }
    },

    engagement: {
        likes: Number,
        shares: Number,
        comments: Number
    },

    location: {
        type: String,
        coordinates: [Number],
        district: String,
        state: String
    },

    posted_at: Date,
    collected_at: Date,

    // Indexes
    // db.social_posts.createIndex({ "posted_at": -1 })
    // db.social_posts.createIndex({ "analysis.topics": 1 })
    // db.social_posts.createIndex({ "location.district": 1 })
}

// sentiment_aggregates - Pre-computed aggregates
{
    _id: ObjectId,
    date: Date,
    granularity: String,        // 'hourly', 'daily', 'weekly'
    region: {
        type: String,           // 'state', 'district'
        name: String
    },
    topic: String,

    metrics: {
        total_posts: Number,
        avg_sentiment: Number,
        sentiment_distribution: {
            positive: Number,
            negative: Number,
            neutral: Number
        },
        volume_change: Number,  // % change from previous period
        trending_score: Number
    },

    top_posts: [{
        post_id: ObjectId,
        content: String,
        engagement: Number
    }],

    created_at: Date
}

// alerts - Sentiment alerts
{
    _id: ObjectId,
    alert_type: String,         // 'spike', 'negative_trend', 'competitor'
    severity: String,           // 'low', 'medium', 'high', 'critical'

    trigger: {
        metric: String,
        threshold: Number,
        actual_value: Number
    },

    context: {
        topic: String,
        region: String,
        sample_posts: [ObjectId]
    },

    status: String,             // 'new', 'acknowledged', 'resolved'
    acknowledged_by: String,

    created_at: Date,
    resolved_at: Date
}
```

### 3. Activity & Engagement Collections

```javascript
// member_activity_logs - Detailed activity tracking
{
    _id: ObjectId,
    member_id: String,
    session_id: String,

    activity: {
        type: String,           // 'login', 'page_view', 'action'
        action: String,         // 'view_event', 'register', 'donate'
        target_type: String,
        target_id: String
    },

    device: {
        type: String,
        os: String,
        browser: String,
        app_version: String
    },

    location: {
        ip: String,
        city: String,
        coordinates: [Number]
    },

    timestamp: Date,

    // TTL index - auto-delete after 90 days
    // db.member_activity_logs.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 })
}

// engagement_analytics - Periodic snapshots
{
    _id: ObjectId,
    date: Date,
    unit_id: String,
    unit_type: String,

    metrics: {
        total_members: Number,
        active_members: Number,         // active in last 30 days
        new_members: Number,
        churned_members: Number,

        avg_engagement_score: Number,

        event_participation: {
            total_events: Number,
            avg_attendance: Number,
            attendance_rate: Number
        },

        donation_metrics: {
            total_donations: Number,
            total_amount: Number,
            avg_donation: Number,
            donor_count: Number
        },

        communication_metrics: {
            announcement_reach: Number,
            discussion_posts: Number,
            grievances_submitted: Number,
            grievances_resolved: Number
        }
    },

    top_engaged_members: [{
        member_id: String,
        score: Number
    }],

    at_risk_members: [{
        member_id: String,
        churn_probability: Number,
        last_activity: Date
    }],

    created_at: Date
}
```

### 4. ML Model Collections

```javascript
// model_registry
{
    _id: ObjectId,
    model_name: String,
    model_type: String,         // 'voter_prediction', 'sentiment', 'churn'
    version: String,

    training: {
        started_at: Date,
        completed_at: Date,
        dataset_size: Number,
        features: [String],
        hyperparameters: Object
    },

    metrics: {
        accuracy: Number,
        precision: Number,
        recall: Number,
        f1_score: Number,
        auc_roc: Number
    },

    artifacts: {
        model_path: String,
        scaler_path: String,
        encoder_path: String
    },

    status: String,             // 'training', 'ready', 'deployed', 'archived'
    deployed_at: Date,

    created_at: Date
}

// prediction_logs
{
    _id: ObjectId,
    model_name: String,
    model_version: String,

    input: Object,
    prediction: Object,
    confidence: Number,

    feedback: {
        actual_outcome: Object,
        correct: Boolean,
        feedback_at: Date
    },

    latency_ms: Number,

    created_at: Date
}
```

---

## Indexes Summary

### PostgreSQL
```sql
-- Performance indexes
CREATE INDEX idx_members_created ON members(created_at DESC);
CREATE INDEX idx_events_start ON events(start_time);
CREATE INDEX idx_events_unit ON events(unit_id);
CREATE INDEX idx_announcements_publish ON announcements(publish_at DESC);
CREATE INDEX idx_grievances_status ON grievances(status, created_at);
CREATE INDEX idx_donations_date ON donations(created_at DESC);

-- Full-text search
CREATE INDEX idx_members_search ON members USING GIN (
    to_tsvector('english', coalesce(first_name, '') || ' ' || coalesce(last_name, ''))
);
```

### MongoDB
```javascript
// Time-series optimization
db.social_posts.createIndex({ "posted_at": -1, "analysis.sentiment_score": 1 });
db.member_activity_logs.createIndex({ "member_id": 1, "timestamp": -1 });
db.sentiment_aggregates.createIndex({ "date": -1, "topic": 1, "region.name": 1 });

// Geospatial
db.social_posts.createIndex({ "location": "2dsphere" });
db.voter_profiles.createIndex({ "address.district": 1, "predicted_affinity.party_score": -1 });
```
