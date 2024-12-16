<!DOCTYPE html>
<html>
<body>

<h1>Upload Cover</h1>

<form action="" method="post" enctype="multipart/form-data">
  Select image to upload:
  <input type="file" name="fileToUpload" id="fileToUpload">
  <input type="submit" value="Upload Image" name="submit">
</form>

<?php
if(isset($_POST["submit"])) {
    $target_dir = "images/current/";
    $target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);
    $imageFileType = strtolower(pathinfo($target_file,PATHINFO_EXTENSION));

    // Get all files in the directory
    $files = glob($target_dir . '*');

    // Sort files by modified time, latest first
    usort($files, function($a, $b) {
        return filemtime($b) - filemtime($a);
    });

    // If there is a previous image, rename it
    if (count($files) > 0) {
        $latest_file = $files[0];
        $id = time(); // Generate an ID based on the current time
        rename($latest_file, $target_dir . 'img_' . $id . '.' . $imageFileType);
    }

    // The new uploaded image will always have the name img.jpg
    $new_filename = $target_dir . 'img.' . $imageFileType;

    if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $new_filename)) {
        // Load the image
        if($imageFileType == "jpg" || $imageFileType == "jpeg"){
            $src = imagecreatefromjpeg($new_filename);
        } else if($imageFileType == "png"){
            $src = imagecreatefrompng($new_filename);
        } else if($imageFileType == "gif"){
            $src = imagecreatefromgif($new_filename);
        }

        // Get the image dimensions
        $width = imagesx($src);
        $height = imagesy($src);

        // Calculate the scaling factor and scaled dimensions
        $scale = max(300 / $width, 400 / $height);
        $scaled_width = $width * $scale;
        $scaled_height = $height * $scale;

        // Create the new image
        $dst = imagecreatetruecolor(300, 400);

        // Resize and crop the image
        imagecopyresampled($dst, $src, 0, 0, ($scaled_width - 300) / 2, ($scaled_height - 400) / 2, $scaled_width, $scaled_height, $width, $height);

        // Save the new image
        if($imageFileType == "jpg" || $imageFileType == "jpeg"){
            imagejpeg($dst, $new_filename);
        } else if($imageFileType == "png"){
            imagepng($dst, $new_filename);
        } else if($imageFileType == "gif"){
            imagegif($dst, $new_filename);
        }

        echo "The file ". basename( $_FILES["fileToUpload"]["name"]). " has been uploaded and resized.";
    } else {
        echo "Sorry, there was an error uploading your file.";
    }
}
?>

</body>
</html>