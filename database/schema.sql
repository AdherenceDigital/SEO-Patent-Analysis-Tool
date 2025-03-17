-- database/schema.sql

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    url TEXT,
    created_at TIMESTAMP NOT NULL
);

-- Uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    upload_type TEXT NOT NULL, -- 'ahrefs', 'screaming_frog', 'search_console'
    filename TEXT NOT NULL,
    notes TEXT,
    uploaded_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);

-- Patents table
CREATE TABLE IF NOT EXISTS patents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    filing_date TEXT,
    issue_date TEXT,
    inventors TEXT,
    assignee TEXT,
    category TEXT,
    full_text TEXT
);

-- Analyses table
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    patent_id TEXT NOT NULL,
    upload_id INTEGER NOT NULL,
    analysis_data TEXT NOT NULL, -- JSON string
    recommendations TEXT NOT NULL, -- JSON string
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects (id),
    FOREIGN KEY (patent_id) REFERENCES patents (patent_id),
    FOREIGN KEY (upload_id) REFERENCES uploads (id)
);

-- Ahrefs backlinks table
CREATE TABLE IF NOT EXISTS ahrefs_backlinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    backlink_url TEXT NOT NULL,
    domain_rating INTEGER,
    url_rating INTEGER,
    anchor_text TEXT,
    first_seen TEXT,
    last_seen TEXT,
    FOREIGN KEY (upload_id) REFERENCES uploads (id)
);

-- Ahrefs internal links table
CREATE TABLE IF NOT EXISTS ahrefs_internal_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    anchor_text TEXT,
    FOREIGN KEY (upload_id) REFERENCES uploads (id)
);

-- Screaming Frog crawl data
CREATE TABLE IF NOT EXISTS screaming_frog_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    status_code INTEGER,
    title TEXT,
    meta_description TEXT,
    h1 TEXT,
    h2 TEXT,
    content_type TEXT,
    word_count INTEGER,
    inlinks INTEGER,
    outlinks INTEGER,
    redirect_url TEXT,
    indexability TEXT,
    FOREIGN KEY (upload_id) REFERENCES uploads (id)
);

-- Search Console data
CREATE TABLE IF NOT EXISTS search_console_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    query TEXT,
    country TEXT,
    device TEXT,
    impressions INTEGER,
    clicks INTEGER,
    position REAL,
    date TEXT,
    FOREIGN KEY (upload_id) REFERENCES uploads (id)
);
