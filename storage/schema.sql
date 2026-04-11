-- storage/schema.sql
create table if not exists sources (
  id integer primary key autoincrement,
  type text not null,
  name text not null unique,
  external_id text not null,
  status text not null default 'active',
  config text not null default '{}',
  created_at text not null,
  updated_at text not null
);

create table if not exists items (
  id integer primary key autoincrement,
  source_id integer not null,
  source_type text not null,
  title text not null,
  url text not null,
  author text,
  published_at text not null,
  raw_content text not null,
  summary text,
  cover text,
  tags text not null default '[]',
  language text not null default 'zh',
  content_hash text not null unique,
  status text not null default 'raw',
  title_zh text not null default '',
  summary_zh text not null default '',
  created_at text not null,
  updated_at text not null,
  foreign key(source_id) references sources(id)
);

create table if not exists topics (
  id integer primary key autoincrement,
  name text not null,
  bundle_date text not null,
  description text not null default '',
  keywords text not null default '[]',
  created_at text not null,
  updated_at text not null,
  unique(name, bundle_date)
);

create table if not exists bundles (
  id integer primary key autoincrement,
  bundle_date text not null unique,
  title text not null,
  intro text not null,
  highlights text not null default '[]',
  status text not null default 'draft',
  created_at text not null,
  updated_at text not null
);

create table if not exists bundle_items (
  bundle_id integer not null,
  item_id integer not null,
  sort_order integer not null,
  primary key(bundle_id, item_id),
  foreign key(bundle_id) references bundles(id),
  foreign key(item_id) references items(id)
);

create table if not exists bundle_topics (
  bundle_id integer not null,
  topic_id integer not null,
  primary key(bundle_id, topic_id),
  foreign key(bundle_id) references bundles(id),
  foreign key(topic_id) references topics(id)
);

create table if not exists publish_tasks (
  id integer primary key autoincrement,
  bundle_id integer not null,
  channel text not null,
  payload text not null,
  status text not null default 'pending',
  scheduled_at text,
  published_at text,
  result text not null default '{}',
  created_at text not null,
  updated_at text not null,
  foreign key(bundle_id) references bundles(id)
);

-- 索引：加速按日期查询和按来源筛选
create index if not exists idx_items_published_at on items(published_at);
create index if not exists idx_items_source_id on items(source_id);
