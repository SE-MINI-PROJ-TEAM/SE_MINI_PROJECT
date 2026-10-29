// k6 performance suite (STP: Performance Testing)
//   TC-PERF-01  SYS-NF-001  95% of standard requests < 800 ms with 500 active sessions
//   TC-PERF-02  SYS-NF-002  200 simultaneous attendance + grade submissions, 0 failures / no deadlock
//
// Run through `python qa/run.py perf` (seeds a QA database, starts waitress, runs this in Docker or native k6).
import http from 'k6/http';
import exec from 'k6/execution';
import { check, sleep } from 'k6';

// One URL, or a comma-separated list of worker processes that requests are spread across (a load balancer stand-in).
const BASES = (__ENV.BASE_URL || 'http://127.0.0.1:5055').split(',');
const BASE = BASES[0];
const api = (n = 0) => `${BASES[n % BASES.length]}/api/v1`;
const API = api();
const JSON_HEADERS = { 'Content-Type': 'application/json' };

export const options = {
  scenarios: {
    // 500 signed-in users browsing with 1-3 s think time between clicks.
    sessions: {
      executor: 'ramping-vus',
      stages: [
        { duration: '15s', target: 500 },
        { duration: '45s', target: 500 },
        { duration: '5s', target: 0 },
      ],
      gracefulRampDown: '10s',
      exec: 'browse',
    },
    // After the browsing load ends: 200 requests released at the same instant.
    burst: {
      executor: 'shared-iterations',
      vus: 200,
      iterations: 200,
      maxDuration: '60s',
      startTime: '80s',
      exec: 'burst',
    },
  },
  thresholds: {
    'http_req_duration{scenario:sessions}': ['p(95)<800'], // SYS-NF-001
    'http_req_failed{scenario:sessions}': ['rate<0.01'],
    'http_req_failed{scenario:burst}': ['rate==0'], // SYS-NF-002: zero failures
    'checks{scenario:burst}': ['rate==1'],
    // Guard against vacuous passes: thresholds on an empty metric succeed, so require real traffic.
    'http_reqs{scenario:sessions}': ['count>1000'],
    'http_reqs{scenario:burst}': ['count>=200'],
    'checks{scenario:sessions}': ['rate>0.99'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

function login(identifier) {
  const res = http.post(`${API}/auth/login`, JSON.stringify({ identifier, password: 'Password@123' }), { headers: JSON_HEADERS });
  if (res.status !== 200) throw new Error(`login failed for ${identifier}: ${res.status}`);
  const token = res.cookies.srs_token[0].value;
  http.cookieJar().clear(BASE); // the session cookie would otherwise override the Bearer header on later calls
  return token;
}

const bearer = (token) => ({ headers: { ...JSON_HEADERS, Authorization: `Bearer ${token}` } });

export function setup() {
  // Real bcrypt (cost 12) logins happen once here, not inside the measured scenarios.
  const students = [];
  for (let i = 1; i <= 30; i++) students.push(login(`student${String(i).padStart(3, '0')}@srs.edu`));
  const faculty = login('faculty001@srs.edu');
  const admin = login('admin001@srs.edu');

  const sessions = http.get(`${API}/attendance/sessions`, bearer(faculty)).json('sessions');
  const open = sessions.find((s) => s.status === 'open');
  const roster = http.get(`${API}/attendance/sessions/${open.id}`, bearer(faculty)).json('students');
  const grid = http.get(`${API}/grades/courses/3`, bearer(faculty)).json();
  return {
    students, faculty, admin,
    sessionId: open.id,
    roster: roster.map((s) => s.student_id),
    courseId: grid.course.id,
    rubricIds: grid.rubric.map((r) => r.id),
    gradeable: grid.students.filter((s) => s.editable).map((s) => s.student_id),
  };
}

const STUDENT_PAGES = ['/catalog', '/analytics/student/summary', '/attendance/summary', '/grades/mine', '/enrollments/mine', '/schedule/calendar'];
const FACULTY_PAGES = ['/analytics/faculty/sections', '/attendance/sessions', '/grades/courses', '/schedule/my-courses'];

export function browse(data) {
  const vu = exec.vu.idInTest;
  // ~1 in 12 sessions is a faculty member, ~1 in 60 an administrator; the rest are students.
  let token = data.students[vu % data.students.length];
  let pages = STUDENT_PAGES;
  if (vu % 60 === 0) { token = data.admin; pages = ['/admin/metrics']; }
  else if (vu % 12 === 0) { token = data.faculty; pages = FACULTY_PAGES; }

  const path = pages[Math.floor(Math.random() * pages.length)];
  const res = http.get(`${api(vu + exec.vu.iterationInInstance)}${path}`, { ...bearer(token), tags: { name: path } });
  const ok = check(res, { 'status 200': (r) => r.status === 200 });
  if (!ok && Math.random() < 0.01) console.error(`browse ${path} -> ${res.status} ${res.error || ''} ${String(res.body).slice(0, 120)}`);
  sleep(1 + Math.random() * 2);
}

export function burst(data) {
  const i = exec.scenario.iterationInTest;
  let res;
  if (i % 2 === 0) {
    // 100 overlapping roll-call submissions for the SAME session: worst case for row locks.
    const list = data.roster.map((id, n) => ({ student_id: id, is_present: (n + i) % 4 !== 0 }));
    res = http.post(`${api(i)}/attendance/sessions/${data.sessionId}`, JSON.stringify({ attendance_list: list }), bearer(data.faculty));
  } else {
    const student = data.gradeable[(i >> 1) % data.gradeable.length];
    const scores = data.rubricIds.map((id, n) => ({ rubric_id: id, score: 50 + ((i + n * 7) % 100) / 2 }));
    res = http.put(`${api(i)}/grades/courses/${data.courseId}/students/${student}`, JSON.stringify({ rubric_scores: scores, target_state: 'Draft' }), bearer(data.faculty));
  }
  const ok = check(res, { 'submission accepted (200)': (r) => r.status === 200 });
  if (!ok && Math.random() < 0.05) console.error(`burst #${i} -> ${res.status} ${res.error || ''} ${String(res.body).slice(0, 160)}`);
}
