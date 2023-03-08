# this script builds my docker images for the mqtt service-stack

# add the images you want to build to the array
$images = @(
    "cpu_logger_mqtt"#,
    # "mongodb_consumer_mqtt",
    # "sensor_logger_fast_api_mqtt"
)

foreach ($image in $images) {
    Write-Host "Building image $image"
    docker build -t $image .\$image
}