<?php
// File: cat/public/asset_create.php
declare(strict_types=1);

require_once __DIR__ . '/../config/db.php';

session_start();

/**
 * when team adds auth later, I need to keep this function and replace the body.
 * For now, it's a no-op so you can demo your page independently.
 */
function require_asset_creator_access(): void
{
    // Example integration later:
    // if (!isset($_SESSION['user'])) { header('Location: /cat/public/login.php'); exit; }
    // if (($_SESSION['user']['role'] ?? '') !== 'admin') { http_response_code(403); exit('403 Forbidden'); }
}

function is_valid_status(string $status): bool
{
    return in_array($status, ['AVAILABLE', 'IN_USE', 'MAINTENANCE', 'RETIRED'], true);
}

function fetch_lookup(string $table): array
{
    $allowed = ['categories', 'locations'];
    if (!in_array($table, $allowed, true)) {
        throw new RuntimeException('Invalid lookup table.');
    }

    return cat_db()->query("SELECT id, name FROM {$table} ORDER BY name")->fetchAll();
}

require_asset_creator_access();

$categories = fetch_lookup('categories');
$locations = fetch_lookup('locations');

$error = null;
$success = null;

$form = [
    'asset_tag' => '',
    'name' => '',
    'serial_number' => '',
    'category_id' => '',
    'location_id' => '',
    'status' => 'AVAILABLE',
    'notes' => '',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach (array_keys($form) as $k) {
        $val = $_POST[$k] ?? '';
        $form[$k] = is_string($val) ? trim($val) : '';
    }

    $categoryId = (int)($form['category_id'] === '' ? 0 : $form['category_id']);
    $locationId = (int)($form['location_id'] === '' ? 0 : $form['location_id']);
    $status = $form['status'];

    if ($form['asset_tag'] === '' || $form['name'] === '') {
        $error = 'Asset Tag and Name are required.';
    } elseif ($categoryId <= 0 || $locationId <= 0) {
        $error = 'Category and Location are required.';
    } elseif (!is_valid_status($status)) {
        $error = 'Invalid status.';
    } else {
        try {
            $stmt = cat_db()->prepare(
                "INSERT INTO assets (asset_tag, name, serial_number, category_id, location_id, status, notes)
                 VALUES (:asset_tag, :name, :serial_number, :category_id, :location_id, :status, :notes)"
            );
            $stmt->execute([
                'asset_tag' => $form['asset_tag'],
                'name' => $form['name'],
                'serial_number' => ($form['serial_number'] === '' ? null : $form['serial_number']),
                'category_id' => $categoryId,
                'location_id' => $locationId,
                'status' => $status,
                'notes' => ($form['notes'] === '' ? null : $form['notes']),
            ]);

            $success = 'Asset created successfully.';
            foreach ($form as $k => $_) {
                $form[$k] = $k === 'status' ? 'AVAILABLE' : '';
            }
        } catch (PDOException $e) {
            $mysqlErr = (int)($e->errorInfo[1] ?? 0);
            if ($mysqlErr === 1062) {
                $error = 'Asset Tag already exists. Please use a unique tag.';
            } else {
                $error = 'Database error: ' . $e->getMessage();
            }
        }
    }
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>CAT - Add Asset</title>
  <style>
    body { font-family: Arial, sans-serif; background:#f6f7fb; margin:0; }
    header { background:#fff; padding:16px 24px; border-bottom:1px solid #eee; }
    .container { max-width:820px; margin:24px auto; padding:0 16px; }
    .card { background:#fff; border:1px solid #eee; border-radius:14px; padding:18px; }
    label { font-size: 13px; color:#333; display:block; margin-top:12px; }
    input, select, textarea { width:100%; padding:12px; margin-top:6px; border:1px solid #ddd; border-radius:10px; }
    button { margin-top:14px; padding:12px 14px; border:0; border-radius:10px; background:#1f5cff; color:#fff; font-weight:700; cursor:pointer; }
    .msg { padding:10px; border-radius:10px; margin-bottom:14px; }
    .err { background:#ffe8e8; border:1px solid #ffb3b3; color:#8a1f1f; }
    .ok  { background:#e8fff0; border:1px solid #b3ffd0; color:#1f6b3a; }
    .row { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
    .hint { font-size: 12px; color:#666; margin-top:8px; }
    code { background:#f1f1f1; padding:2px 6px; border-radius:6px; }
  </style>
</head>
<body>
<header>
  <b>Campus Asset Tracker</b> — Add New Asset
  <span class="hint" style="margin-left:12px;">URL: <code>/cat/public/asset_create.php</code></span>
</header>

<div class="container">
  <div class="card">
    <?php if ($error): ?><div class="msg err"><?= htmlspecialchars($error) ?></div><?php endif; ?>
    <?php if ($success): ?><div class="msg ok"><?= htmlspecialchars($success) ?></div><?php endif; ?>

    <form method="post" novalidate>
      <div class="row">
        <div>
          <label>Asset Tag *</label>
          <input name="asset_tag" value="<?= htmlspecialchars($form['asset_tag']) ?>" placeholder="A001" required />
        </div>
        <div>
          <label>Status *</label>
          <select name="status" required>
            <?php foreach (['AVAILABLE','IN_USE','MAINTENANCE','RETIRED'] as $s): ?>
              <option value="<?= $s ?>" <?= $form['status'] === $s ? 'selected' : '' ?>><?= $s ?></option>
            <?php endforeach; ?>
          </select>
        </div>
      </div>

      <label>Name *</label>
      <input name="name" value="<?= htmlspecialchars($form['name']) ?>" placeholder="Dell Latitude 5520 Laptop" required />

      <label>Serial Number</label>
      <input name="serial_number" value="<?= htmlspecialchars($form['serial_number']) ?>" placeholder="DL5520-2024-..." />

      <div class="row">
        <div>
          <label>Category *</label>
          <select name="category_id" required>
            <option value="">Select...</option>
            <?php foreach ($categories as $c): ?>
              <option value="<?= (int)$c['id'] ?>" <?= (string)$c['id'] === $form['category_id'] ? 'selected' : '' ?>>
                <?= htmlspecialchars($c['name']) ?>
              </option>
            <?php endforeach; ?>
          </select>
        </div>
        <div>
          <label>Location *</label>
          <select name="location_id" required>
            <option value="">Select...</option>
            <?php foreach ($locations as $l): ?>
              <option value="<?= (int)$l['id'] ?>" <?= (string)$l['id'] === $form['location_id'] ? 'selected' : '' ?>>
                <?= htmlspecialchars($l['name']) ?>
              </option>
            <?php endforeach; ?>
          </select>
        </div>
      </div>

      <label>Notes</label>
      <textarea name="notes" rows="4" placeholder="Optional notes..."><?= htmlspecialchars($form['notes']) ?></textarea>

      <button type="submit">Create Asset</button>
      <div class="hint">Demo tip: submit A001 once (success), then again (unique-tag error).</div>
    </form>
  </div>
</div>
</body>
</html>
