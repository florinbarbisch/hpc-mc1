# this script builds my docker images for the kafka service-stack

# add the images you want to build to the array
$images = @(
    "cpu_logger_kafka",
    "mongodb_consumer_kafka",
    "sensor_logger_fast_api_kafka"
)

foreach ($image in $images) {
    Write-Host "Building image $image"
    docker build -t $image .\$image
}