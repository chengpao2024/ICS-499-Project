<?php
// File: ICS-499-Project/public/asset_create.php
declare(strict_types=1);

require_once __DIR__ . '/../config/db.php'; // your mysqli $conn

session_start();

function require_asset_creator_access(): void
{
    // Placeholder for future auth
    // Example:
    // if (!isset($_SESSION['user'])) { header('Location: login.php'); exit; }
}

// Allowed statuses
$allowed_statuses = ['available','in-use','maintenance'];

// Require access
require_asset_creator_access();

$error = '';
$success = '';

$form = [
    'asset_name' => '',
    'asset_category' => '',
    'asset_serial' => '',
    'asset_location' => '',
    'asset_status' => 'available',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($form as $k => $_) {
        $form[$k] = trim($_POST[$k] ?? '');
    }

    // Validate
    if ($form['asset_name'] === '' || $form['asset_category'] === '' || $form['asset_location'] === '') {
        $error = 'Asset Name, Category, and Location are required.';
    } elseif (!in_array($form['asset_status'], $allowed_statuses, true)) {
        $error = 'Invalid status selected.';
    } else {
        // Insert into database
        $stmt = $conn->prepare("INSERT INTO assets (asset_name, asset_category, asset_serial, asset_location, asset_status) VALUES (?, ?, ?, ?, ?)");
        if (!$stmt) {
            $error = 'Prepare failed: ' . $conn->error;
        } else {
            $stmt->bind_param(
                'sssss',
                $form['asset_name'],
                $form['asset_category'],
                $form['asset_serial'],
                $form['asset_location'],
                $form['asset_status']
            );
            if ($stmt->execute()) {
                $success = 'Asset created successfully.';
                // Reset form
                $form = [
                    'asset_name' => '',
                    'asset_category' => '',
                    'asset_serial' => '',
                    'asset_location' => '',
                    'asset_status' => 'available',
                ];
            } else {
                $error = 'Database error: ' . $stmt->error;
            }
            $stmt->close();
        }
    }
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CAT - Add Asset</title>
<style>
body { font-family: Arial, sans-serif; background:#f6f7fb; margin:0; }
header { background:#fff; padding:16px 24px; border-bottom:1px solid #eee; }
.container { max-width:600px; margin:24px auto; padding:0 16px; }
.card { background:#fff; border:1px solid #eee; border-radius:14px; padding:18px; }
label { font-size: 13px; color:#333; display:block; margin-top:12px; }
input, select { width:100%; padding:12px; margin-top:6px; border:1px solid #ddd; border-radius:10px; }
button { margin-top:14px; padding:12px 14px; border:0; border-radius:10px; background:#1f5cff; color:#fff; font-weight:700; cursor:pointer; }
.msg { padding:10px; border-radius:10px; margin-bottom:14px; }
.err { background:#ffe8e8; border:1px solid #ffb3b3; color:#8a1f1f; }
.ok { background:#e8fff0; border:1px solid #b3ffd0; color:#1f6b3a; }
</style>
</head>
<body>
<header>
  <b>Campus Asset Tracker</b> — Add New Asset
</header>

<div class="container">
  <div class="card">
    <?php if ($error): ?><div class="msg err"><?= htmlspecialchars($error) ?></div><?php endif; ?>
    <?php if ($success): ?><div class="msg ok"><?= htmlspecialchars($success) ?></div><?php endif; ?>

    <form method="post" novalidate>
        <label>Asset Name *</label>
        <input name="asset_name" value="<?= htmlspecialchars($form['asset_name']) ?>" required>

        <label>Asset Category *</label>
        <input name="asset_category" value="<?= htmlspecialchars($form['asset_category']) ?>" required>

        <label>Asset Serial</label>
        <input name="asset_serial" value="<?= htmlspecialchars($form['asset_serial']) ?>">

        <label>Asset Location *</label>
        <input name="asset_location" value="<?= htmlspecialchars($form['asset_location']) ?>" required>

        <label>Asset Status *</label>
        <select name="asset_status" required>
            <?php foreach ($allowed_statuses as $status): ?>
                <option value="<?= $status ?>" <?= $form['asset_status'] === $status ? 'selected' : '' ?>><?= $status ?></option>
            <?php endforeach; ?>
        </select>

        <button type="submit">Create Asset</button>
    </form>
  </div>
</div>
</body>
</html>