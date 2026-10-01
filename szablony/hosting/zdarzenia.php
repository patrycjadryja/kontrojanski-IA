<?php
// Podglad zdarzen dla panelu generatora: GET ?k=<sekret>&p=<klient>. Zwraca JSON.
$cfg = @include __DIR__ . '/_config.php';
$cfg = is_array($cfg) ? $cfg : [];
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
if (empty($cfg['sekret']) || !hash_equals($cfg['sekret'], (string)($_GET['k'] ?? ''))) { http_response_code(403); echo '{"blad":"brak dostepu"}'; exit; }
$p = preg_replace('/[^a-z0-9\-]/', '', strtolower($_GET['p'] ?? ''));
if ($p === '') { http_response_code(400); echo '{"blad":"brak klienta"}'; exit; }
$plik = __DIR__ . '/_zdarzenia/' . $p . '.csv';
$out = ['klient' => $p, 'zdarzenia' => [], 'akceptacje' => 0];
if (is_readable($plik)) {
    foreach (array_slice(file($plik, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES), -400) as $l) {
        $c = explode(';', $l);
        if (count($c) >= 3) $out['zdarzenia'][] = ['kiedy' => $c[0], 'sesja' => $c[1], 'co' => $c[2]];
    }
}
$a = __DIR__ . '/_zdarzenia/' . $p . '.akceptacje.csv';
if (is_readable($a)) $out['akceptacje'] = count(file($a, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES));
echo json_encode($out, JSON_UNESCAPED_UNICODE);
