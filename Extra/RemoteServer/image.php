<?php
$folder_path = 'images/current/';

// Get all files in the directory
$files = glob($folder_path . '*');

// Sort files by modified time, latest first
usort($files, function($a, $b) {
    return filemtime($b) - filemtime($a);
});

// Get the most recently created file
$latest_file = $files[0];

// Generate a hash based on the file's modified time
$hash = filemtime($latest_file);

// Redirect to the latest file with the hash appended
header('Location: ' . $latest_file . '?' . $hash);
exit;
?>