-- AION minimal schema (Render Postgres)

create table if not exists aion_state (
  user_id        bigint primary key,
  ui_message_id  bigint,
  step           text,
  mode           text,
  payload_json   jsonb,
  updated_at     timestamptz default now()
);

create table if not exists biotime_entries (
  id                 bigserial primary key,
  user_id            bigint not null,
  date               date not null,

  sleep_index        numeric,
  stress_index       numeric,
  recovery_index     numeric,

  pressure_sys_am    numeric,
  pressure_dia_am    numeric,
  pulse_am           numeric,

  pressure_sys_pre   numeric,
  pressure_dia_pre   numeric,
  pulse_pre          numeric,

  pressure_penalty   numeric,
  drop3_penalty      numeric,
  risk_penalty       numeric,

  biotime            numeric,
  aion_index         integer,
  risk30             numeric,
  zone               text,

  protocol_training  text,
  protocol_sleep     text,
  protocol_nutrition text,

  created_at         timestamptz default now(),

  constraint biotime_entries_user_date_uniq unique (user_id, date)
);

create index if not exists biotime_entries_user_date_idx
  on biotime_entries (user_id, date desc);
