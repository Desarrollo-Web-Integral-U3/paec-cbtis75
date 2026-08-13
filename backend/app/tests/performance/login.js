import http from "k6/http";
import { check, sleep } from 'k6';

export const options = {
    vus: 20,
    duration: '30s',
};

const URL = 'https://paec-cbtis75-production.up.railway.app/api/v1/auth/login';
const PAYLOAD = JSON.stringify({
email: 'estudiante1@cbtis75.edu.mx',
password: 'Demo1234!',
});
const HEADERS = { 'Content-Type': 'application/json' };

export default function () {
const res = http.post(URL, PAYLOAD, { headers: HEADERS });
check(res, { 'status is 200': (r) => r.status === 200 });
sleep(1);
}