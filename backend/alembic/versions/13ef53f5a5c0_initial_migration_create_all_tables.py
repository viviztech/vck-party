"""Initial migration - create all tables

Revision ID: 13ef53f5a5c0
Revises: None
Create Date: 2026-01-14 10:14:04.185435+00:00

"""
from typing import Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = '13ef53f5a5c0'
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    """Create all tables based on SQLAlchemy models.
    
    Tables are created in order of their foreign key dependencies.
    """
    
    # =========================================================================
    # Auth Tables (no FK dependencies)
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS permissions (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        resource VARCHAR(50) NOT NULL,
        action VARCHAR(50) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS roles (
        id UUID PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        is_system BOOLEAN DEFAULT FALSE,
        priority INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY,
        phone VARCHAR(15) UNIQUE,
        email VARCHAR(255) UNIQUE,
        password_hash VARCHAR(255),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        is_verified BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        last_login_at TIMESTAMP WITH TIME ZONE,
        last_login_ip VARCHAR(45),
        login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS user_roles (
        user_id UUID NOT NULL,
        role_id UUID NOT NULL,
        assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        assigned_by UUID,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS role_permissions (
        role_id UUID NOT NULL,
        permission_id UUID NOT NULL,
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
        FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS refresh_tokens (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        token_hash VARCHAR(255) NOT NULL UNIQUE,
        token_jti VARCHAR(64) NOT NULL UNIQUE,
        device_info TEXT,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        revoked_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""")
    
    # =========================================================================
    # Organization Hierarchy Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS organization_units (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        code VARCHAR(50) UNIQUE,
        type VARCHAR(50) NOT NULL,
        parent_id UUID,
        level INTEGER DEFAULT 0,
        path VARCHAR(500),
        leader_id UUID,
        contact_phone VARCHAR(15),
        contact_email VARCHAR(255),
        address TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS constituencies (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        code VARCHAR(50) UNIQUE,
        type VARCHAR(50),
        state VARCHAR(100),
        district VARCHAR(100),
        assembly_segment VARCHAR(100),
        parliamentary_constituency VARCHAR(100),
        pincode VARCHAR(20),
        population INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS districts (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        state VARCHAR(100) NOT NULL,
        code VARCHAR(50) UNIQUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS wards (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        code VARCHAR(50),
        district_id UUID,
        municipality_type VARCHAR(50),
        number INTEGER,
        population INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS booths (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        booth_number VARCHAR(20) NOT NULL,
        constituency_id UUID,
        ward_id UUID,
        location TEXT,
        address TEXT,
        pincode VARCHAR(20),
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        total_voters INTEGER DEFAULT 0,
        male_voters INTEGER DEFAULT 0,
        female_voters INTEGER DEFAULT 0,
        other_voters INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (constituency_id) REFERENCES constituencies(id) ON DELETE SET NULL,
        FOREIGN KEY (ward_id) REFERENCES wards(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS zipcode_mapping (
        id UUID PRIMARY KEY,
        pincode VARCHAR(20) NOT NULL,
        district VARCHAR(100),
        state VARCHAR(100),
        taluk VARCHAR(100),
        area_name VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS hierarchy_relations (
        id UUID PRIMARY KEY,
        parent_type VARCHAR(50) NOT NULL,
        parent_id UUID NOT NULL,
        child_type VARCHAR(50) NOT NULL,
        child_id UUID NOT NULL,
        relation_type VARCHAR(50) DEFAULT 'contains',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (parent_type, parent_id, child_type, child_id)
    )""")
    
    # =========================================================================
    # Member Profile Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_tag_definitions (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        color VARCHAR(7),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_skill_definitions (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        category VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_profiles (
        id UUID PRIMARY KEY,
        user_id UUID UNIQUE,
        membership_number VARCHAR(50) UNIQUE,
        first_name VARCHAR(100) NOT NULL,
        middle_name VARCHAR(100),
        last_name VARCHAR(100) NOT NULL,
        gender VARCHAR(20),
        date_of_birth DATE,
        blood_group VARCHAR(10),
        aadhaar_number VARCHAR(12) UNIQUE,
        photo_url TEXT,
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(100),
        district VARCHAR(100),
        constituency VARCHAR(200),
        booth VARCHAR(100),
        pincode VARCHAR(20),
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        phone VARCHAR(15),
        alternate_phone VARCHAR(15),
        email VARCHAR(255),
        education VARCHAR(100),
        profession VARCHAR(100),
        occupation VARCHAR(100),
        employer_name VARCHAR(200),
        employer_address TEXT,
        annual_income VARCHAR(50),
        caste VARCHAR(100),
        religion VARCHAR(100),
        mother_tongue VARCHAR(50),
        nationality VARCHAR(50) DEFAULT 'Indian',
        voting_constituency VARCHAR(200),
        section VARCHAR(50),
        part_number INTEGER,
        serial_number INTEGER,
        booth_number VARCHAR(50),
        epic_number VARCHAR(50),
        membership_status VARCHAR(50) DEFAULT 'active',
        membership_type VARCHAR(50) DEFAULT 'general',
        join_date DATE,
        active_from DATE,
        verified_at TIMESTAMP WITH TIME ZONE,
        verified_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_tags (
        member_id UUID NOT NULL,
        tag_id UUID NOT NULL,
        assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        assigned_by UUID,
        PRIMARY KEY (member_id, tag_id),
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES member_tag_definitions(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_skills (
        member_id UUID NOT NULL,
        skill_id UUID NOT NULL,
        proficiency_level INTEGER DEFAULT 1,
        years_experience INTEGER,
        verified BOOLEAN DEFAULT FALSE,
        verified_by UUID,
        verified_at TIMESTAMP WITH TIME ZONE,
        PRIMARY KEY (member_id, skill_id),
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES member_skill_definitions(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_families (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL,
        relation VARCHAR(50) NOT NULL,
        name VARCHAR(200) NOT NULL,
        age INTEGER,
        gender VARCHAR(20),
        occupation VARCHAR(100),
        is_voter BOOLEAN DEFAULT FALSE,
        epic_number VARCHAR(50),
        phone VARCHAR(15),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_documents (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL,
        document_type VARCHAR(50) NOT NULL,
        document_number VARCHAR(100),
        file_url TEXT NOT NULL,
        file_name VARCHAR(255),
        file_type VARCHAR(50),
        file_size INTEGER,
        is_verified BOOLEAN DEFAULT FALSE,
        verified_by UUID,
        verified_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS member_notes (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL,
        note_type VARCHAR(50) NOT NULL,
        content TEXT NOT NULL,
        created_by UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS membership_history (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL,
        action VARCHAR(50) NOT NULL,
        previous_status VARCHAR(50),
        new_status VARCHAR(50),
        reason TEXT,
        changed_by UUID,
        changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS members (
        id UUID PRIMARY KEY,
        user_id UUID UNIQUE,
        unit_id UUID,
        member_type VARCHAR(50) DEFAULT 'general',
        membership_number VARCHAR(50) UNIQUE,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        phone VARCHAR(15),
        email VARCHAR(255),
        status VARCHAR(20) DEFAULT 'active',
        joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL
    )""")
    
    # =========================================================================
    # Events and Campaigns Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS events (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        event_type VARCHAR(50) NOT NULL,
        unit_id UUID,
        organizer_id UUID,
        start_date TIMESTAMP WITH TIME ZONE NOT NULL,
        end_date TIMESTAMP WITH TIME ZONE,
        location TEXT,
        address TEXT,
        city VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(20),
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
        is_virtual BOOLEAN DEFAULT FALSE,
        virtual_meeting_url TEXT,
        max_participants INTEGER,
        registration_required BOOLEAN DEFAULT FALSE,
        registration_deadline TIMESTAMP WITH TIME ZONE,
        status VARCHAR(20) DEFAULT 'draft',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (organizer_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS event_participants (
        id UUID PRIMARY KEY,
        event_id UUID NOT NULL,
        member_id UUID,
        user_id UUID,
        name VARCHAR(200) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(15),
        registration_status VARCHAR(20) DEFAULT 'registered',
        registration_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        attendance_status VARCHAR(20) DEFAULT 'pending',
        check_in_time TIMESTAMP WITH TIME ZONE,
        check_out_time TIMESTAMP WITH TIME ZONE,
        feedback TEXT,
        rating INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS event_attendance (
        id UUID PRIMARY KEY,
        event_id UUID NOT NULL,
        member_id UUID NOT NULL,
        check_in_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        check_out_time TIMESTAMP WITH TIME ZONE,
        check_in_method VARCHAR(20) DEFAULT 'manual',
        verified_by UUID,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS event_tasks (
        id UUID PRIMARY KEY,
        event_id UUID NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        assigned_to_id UUID,
        status VARCHAR(20) DEFAULT 'pending',
        priority VARCHAR(20) DEFAULT 'medium',
        due_date TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS event_budgets (
        id UUID PRIMARY KEY,
        event_id UUID NOT NULL,
        category VARCHAR(100) NOT NULL,
        description TEXT,
        estimated_amount DECIMAL(12, 2) DEFAULT 0,
        actual_amount DECIMAL(12, 2) DEFAULT 0,
        approved_amount DECIMAL(12, 2) DEFAULT 0,
        status VARCHAR(20) DEFAULT 'draft',
        approved_by UUID,
        approved_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS event_feedback (
        id UUID PRIMARY KEY,
        event_id UUID NOT NULL,
        member_id UUID,
        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
        feedback TEXT,
        suggestion TEXT,
        is_anonymous BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS campaigns (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        campaign_type VARCHAR(50) NOT NULL,
        unit_id UUID,
        start_date DATE NOT NULL,
        end_date DATE,
        target_metrics JSONB DEFAULT '{}',
        current_metrics JSONB DEFAULT '{}',
        status VARCHAR(20) DEFAULT 'draft',
        is_active BOOLEAN DEFAULT TRUE,
        created_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS campaign_tasks (
        id UUID PRIMARY KEY,
        campaign_id UUID NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        task_type VARCHAR(50),
        assigned_to_id UUID,
        status VARCHAR(20) DEFAULT 'pending',
        priority VARCHAR(20) DEFAULT 'medium',
        due_date DATE,
        target_count INTEGER,
        completed_count INTEGER DEFAULT 0,
        location TEXT,
        notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    # =========================================================================
    # Communications Tables (includes Grievances)
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS announcements (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        announcement_type VARCHAR(50) DEFAULT 'general',
        priority VARCHAR(20) DEFAULT 'normal',
        author_id UUID NOT NULL,
        unit_id UUID,
        is_published BOOLEAN DEFAULT FALSE,
        published_at TIMESTAMP WITH TIME ZONE,
        expires_at TIMESTAMP WITH TIME ZONE,
        target_audience JSONB DEFAULT '"all"',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS announcement_targets (
        id UUID PRIMARY KEY,
        announcement_id UUID NOT NULL,
        target_type VARCHAR(50) NOT NULL,
        target_id UUID NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        read_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (announcement_id) REFERENCES announcements(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS forums (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        forum_type VARCHAR(50) DEFAULT 'general',
        visibility VARCHAR(20) DEFAULT 'public',
        unit_id UUID,
        created_by UUID NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        last_activity_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS forum_posts (
        id UUID PRIMARY KEY,
        forum_id UUID NOT NULL,
        author_id UUID NOT NULL,
        parent_post_id UUID,
        title VARCHAR(255),
        content TEXT NOT NULL,
        post_type VARCHAR(20) DEFAULT 'post',
        is_pinned BOOLEAN DEFAULT FALSE,
        is_locked BOOLEAN DEFAULT FALSE,
        view_count INTEGER DEFAULT 0,
        reply_count INTEGER DEFAULT 0,
        last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (forum_id) REFERENCES forums(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_post_id) REFERENCES forum_posts(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS forum_comments (
        id UUID PRIMARY KEY,
        post_id UUID NOT NULL,
        author_id UUID NOT NULL,
        parent_comment_id UUID,
        content TEXT NOT NULL,
        is_approved BOOLEAN DEFAULT TRUE,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES forum_posts(id) ON DELETE CASCADE,
        FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_comment_id) REFERENCES forum_comments(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS forum_reactions (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        reaction_type VARCHAR(20) NOT NULL,
        post_id UUID,
        comment_id UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (user_id, post_id),
        UNIQUE (user_id, comment_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (post_id) REFERENCES forum_posts(id) ON DELETE CASCADE,
        FOREIGN KEY (comment_id) REFERENCES forum_comments(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS grievances (
        id UUID PRIMARY KEY,
        ticket_number VARCHAR(50) NOT NULL UNIQUE,
        member_id UUID NOT NULL,
        unit_id UUID,
        category VARCHAR(100) NOT NULL,
        subject VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        priority VARCHAR(20) DEFAULT 'medium',
        status VARCHAR(20) DEFAULT 'submitted',
        assigned_to_id UUID,
        resolution_summary TEXT,
        member_feedback TEXT,
        rating INTEGER,
        resolved_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_to_id) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS grievance_updates (
        id UUID PRIMARY KEY,
        grievance_id UUID NOT NULL,
        status_from VARCHAR(20),
        status_to VARCHAR(20) NOT NULL,
        notes TEXT,
        updated_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grievance_id) REFERENCES grievances(id) ON DELETE CASCADE,
        FOREIGN KEY (updated_by) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS grievance_attachments (
        id UUID PRIMARY KEY,
        grievance_id UUID NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path TEXT NOT NULL,
        file_type VARCHAR(100),
        file_size INTEGER,
        uploaded_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grievance_id) REFERENCES grievances(id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS communication_logs (
        id UUID PRIMARY KEY,
        recipient_id UUID NOT NULL,
        recipient_phone VARCHAR(15),
        recipient_email VARCHAR(255),
        communication_type VARCHAR(50) NOT NULL,
        subject VARCHAR(255),
        content TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        sent_at TIMESTAMP WITH TIME ZONE,
        delivered_at TIMESTAMP WITH TIME ZONE,
        opened_at TIMESTAMP WITH TIME ZONE,
        failed_reason TEXT,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # =========================================================================
    # Voting Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_positions (
        id UUID PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        election_type VARCHAR(50) DEFAULT 'general',
        max_candidates INTEGER,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS elections (
        id UUID PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        election_type VARCHAR(50) NOT NULL,
        unit_id UUID,
        start_date TIMESTAMP WITH TIME ZONE NOT NULL,
        end_date TIMESTAMP WITH TIME ZONE NOT NULL,
        voting_start_time TIMESTAMP WITH TIME ZONE,
        voting_end_time TIMESTAMP WITH TIME ZONE,
        status VARCHAR(20) DEFAULT 'draft',
        is_secret BOOLEAN DEFAULT TRUE,
        allow_proxy BOOLEAN DEFAULT FALSE,
        max_proxies_per_member INTEGER,
        min_candidates INTEGER,
        election_rules TEXT,
        created_by UUID NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_position_association (
        election_id UUID NOT NULL,
        position_id UUID NOT NULL,
        PRIMARY KEY (election_id, position_id),
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE
    )"")
        position_id UUID NOT NULL,
        PRIMARY KEY (election_id, position_id),
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_nominations (
        id UUID PRIMARY KEY,
        election_id UUID NOT NULL,
        position_id UUID NOT NULL,
        candidate_id UUID NOT NULL,
        nominator_id UUID NOT NULL,
        nomination_statement TEXT,
        status VARCHAR(20) DEFAULT 'pending',
        proposed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        seconded_at TIMESTAMP WITH TIME ZONE,
        approved_at TIMESTAMP WITH TIME ZONE,
        rejected_reason TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (nominator_id) REFERENCES member_profiles(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_candidates (
        id UUID PRIMARY KEY,
        nomination_id UUID NOT NULL UNIQUE,
        election_id UUID NOT NULL,
        position_id UUID NOT NULL,
        member_id UUID NOT NULL,
        symbol VARCHAR(100),
        symbol_image TEXT,
        election_symbol_id VARCHAR(50),
        campaign_statement TEXT,
        assets JSONB DEFAULT '{}',
        status VARCHAR(20) DEFAULT 'approved',
        vote_count INTEGER DEFAULT 0,
        declared_winner BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (nomination_id) REFERENCES election_nominations(id) ON DELETE CASCADE,
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_voters (
        id UUID PRIMARY KEY,
        election_id UUID NOT NULL,
        member_id UUID NOT NULL,
        voter_number INTEGER,
        has_voted BOOLEAN DEFAULT FALSE,
        voted_at TIMESTAMP WITH TIME ZONE,
        proxy_for_id UUID,
        proxy_assigned_by UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (election_id, member_id),
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE,
        FOREIGN KEY (proxy_for_id) REFERENCES member_profiles(id) ON DELETE SET NULL,
        FOREIGN KEY (proxy_assigned_by) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_votes (
        id UUID PRIMARY KEY,
        election_id UUID NOT NULL,
        position_id UUID NOT NULL,
        voter_id UUID NOT NULL,
        candidate_id UUID NOT NULL,
        vote_token VARCHAR(100) UNIQUE,
        vote_hash VARCHAR(256),
        voted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        vote_method VARCHAR(20) DEFAULT 'online',
        ip_address VARCHAR(45),
        device_info TEXT,
        is_valid BOOLEAN DEFAULT TRUE,
        invalid_reason TEXT,
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (voter_id) REFERENCES election_voters(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES election_candidates(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS vote_proofs (
        id UUID PRIMARY KEY,
        vote_id UUID NOT NULL UNIQUE,
        proof_type VARCHAR(50) NOT NULL,
        proof_value TEXT NOT NULL,
        signature TEXT,
        verified BOOLEAN DEFAULT FALSE,
        verified_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vote_id) REFERENCES election_votes(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS election_results (
        id UUID PRIMARY KEY,
        election_id UUID NOT NULL,
        position_id UUID NOT NULL,
        candidate_id UUID NOT NULL,
        total_votes INTEGER DEFAULT 0,
        percentage DECIMAL(5, 2),
        rank INTEGER,
        is_winner BOOLEAN DEFAULT FALSE,
        margin_of_votes INTEGER,
        declared_at TIMESTAMP WITH TIME ZONE,
        certified_by UUID,
        certification_document TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (election_id) REFERENCES elections(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES election_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES election_candidates(id) ON DELETE CASCADE,
        FOREIGN KEY (certified_by) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    # =========================================================================
    # Donations Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS donation_campaigns (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        unit_id UUID,
        created_by_id UUID,
        target_amount DECIMAL(12, 2) DEFAULT 0,
        collected_amount DECIMAL(12, 2) DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'INR',
        start_date TIMESTAMP WITH TIME ZONE NOT NULL,
        end_date TIMESTAMP WITH TIME ZONE,
        status VARCHAR(20) DEFAULT 'draft',
        is_active BOOLEAN DEFAULT TRUE,
        banner_url TEXT,
        extra_data JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (unit_id) REFERENCES organization_units(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS donations (
        id UUID PRIMARY KEY,
        campaign_id UUID,
        member_id UUID,
        amount DECIMAL(12, 2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'INR',
        donation_type VARCHAR(50) DEFAULT 'general',
        payment_method VARCHAR(50),
        payment_gateway VARCHAR(50),
        transaction_id VARCHAR(255),
        payment_order_id VARCHAR(255),
        payment_status VARCHAR(20) DEFAULT 'pending',
        donor_name VARCHAR(255),
        donor_phone VARCHAR(15),
        donor_email VARCHAR(255),
        donor_pan VARCHAR(20),
        receipt_number VARCHAR(50),
        receipt_url TEXT,
        notes TEXT,
        is_anonymous BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES donation_campaigns(id) ON DELETE SET NULL,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS donation_receipts (
        id UUID PRIMARY KEY,
        donation_id UUID NOT NULL UNIQUE,
        campaign_id UUID,
        receipt_number VARCHAR(50) NOT NULL UNIQUE,
        amount DECIMAL(12, 2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'INR',
        donor_name VARCHAR(255),
        donor_address TEXT,
        donor_pan VARCHAR(20),
        receipt_url TEXT,
        receipt_pdf_path TEXT,
        is_tax_deductible BOOLEAN DEFAULT TRUE,
        tax_section VARCHAR(50),
        generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        generated_by_id UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
        FOREIGN KEY (campaign_id) REFERENCES donation_campaigns(id) ON DELETE SET NULL,
        FOREIGN KEY (generated_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS payment_transactions (
        id UUID PRIMARY KEY,
        donation_id UUID NOT NULL,
        transaction_type VARCHAR(50) DEFAULT 'payment',
        payment_gateway VARCHAR(50),
        gateway_transaction_id VARCHAR(255),
        gateway_order_id VARCHAR(255),
        gateway_payment_id VARCHAR(255),
        gateway_refund_id VARCHAR(255),
        amount DECIMAL(12, 2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'INR',
        status VARCHAR(20) DEFAULT 'pending',
        status_message TEXT,
        request_data JSONB DEFAULT '{}',
        response_data JSONB DEFAULT '{}',
        error_code VARCHAR(100),
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP WITH TIME ZONE,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS donor_reports (
        id UUID PRIMARY KEY,
        report_type VARCHAR(50) NOT NULL,
        member_id UUID NOT NULL,
        period_start TIMESTAMP WITH TIME ZONE NOT NULL,
        period_end TIMESTAMP WITH TIME ZONE NOT NULL,
        total_donations INTEGER DEFAULT 0,
        total_amount DECIMAL(12, 2) DEFAULT 0,
        currency VARCHAR(3) DEFAULT 'INR',
        by_campaign JSONB DEFAULT '{}',
        by_month JSONB DEFAULT '{}',
        report_url TEXT,
        generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES member_profiles(id) ON DELETE CASCADE
    )""")
    
    # =========================================================================
    # Workers/Task Queue Tables
    # =========================================================================
    
    op.execute("""CREATE TABLE IF NOT EXISTS task_queue (
        id UUID PRIMARY KEY,
        task_type VARCHAR(50) NOT NULL,
        task_name VARCHAR(255) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        priority INTEGER DEFAULT 3,
        payload JSONB DEFAULT '{}',
        extra_data JSONB DEFAULT '{}',
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        worker_id VARCHAR(255),
        result JSONB DEFAULT '{}',
        error_message TEXT,
        error_traceback TEXT,
        scheduled_at TIMESTAMP WITH TIME ZONE,
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS task_history (
        id UUID PRIMARY KEY,
        task_id UUID NOT NULL,
        attempt_number INTEGER DEFAULT 1,
        status VARCHAR(20) NOT NULL,
        worker_id VARCHAR(255),
        worker_host VARCHAR(255),
        started_at TIMESTAMP WITH TIME ZONE,
        completed_at TIMESTAMP WITH TIME ZONE,
        duration_ms INTEGER,
        input_payload JSONB DEFAULT '{}',
        output_result JSONB DEFAULT '{}',
        error_message TEXT,
        error_traceback TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES task_queue(id) ON DELETE CASCADE
    )""")
    
    op.execute("""CREATE TABLE IF NOT EXISTS scheduled_tasks (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        task_type VARCHAR(50) NOT NULL,
        task_name VARCHAR(255) NOT NULL,
        payload JSONB DEFAULT '{}',
        extra_data JSONB DEFAULT '{}',
        cron_expression VARCHAR(100) NOT NULL,
        timezone VARCHAR(50) DEFAULT 'UTC',
        status VARCHAR(20) DEFAULT 'active',
        max_retries INTEGER DEFAULT 3,
        retry_delay_seconds INTEGER DEFAULT 60,
        timeout_seconds INTEGER DEFAULT 300,
        last_run_at TIMESTAMP WITH TIME ZONE,
        last_run_status VARCHAR(20),
        last_run_result JSONB DEFAULT '{}',
        last_error TEXT,
        next_run_at TIMESTAMP WITH TIME ZONE,
        created_by_id UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
    )""")


def downgrade() -> None:
    """Drop all tables in reverse order."""
    tables = [
        'scheduled_tasks',
        'task_history',
        'task_queue',
        'donor_reports',
        'payment_transactions',
        'donation_receipts',
        'donations',
        'donation_campaigns',
        'election_results',
        'vote_proofs',
        'election_votes',
        'election_voters',
        'election_candidates',
        'election_nominations',
        'election_position_association',
        'elections',
        'election_positions',
        'communication_logs',
        'grievance_attachments',
        'grievance_updates',
        'grievances',
        'forum_reactions',
        'forum_comments',
        'forum_posts',
        'forums',
        'announcement_targets',
        'announcements',
        'campaign_tasks',
        'campaigns',
        'event_feedback',
        'event_budgets',
        'event_tasks',
        'event_attendance',
        'event_participants',
        'events',
        'membership_history',
        'member_notes',
        'member_documents',
        'member_families',
        'member_skills',
        'member_tags',
        'member_profiles',
        'member_skill_definitions',
        'member_tag_definitions',
        'members',
        'hierarchy_relations',
        'zipcode_mapping',
        'booths',
        'wards',
        'districts',
        'constituencies',
        'organization_units',
        'refresh_tokens',
        'role_permissions',
        'user_roles',
        'users',
        'roles',
        'permissions',
    ]
    
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
