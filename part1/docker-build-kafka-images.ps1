# build each image in the following folders
# - .\cpu_logger_kafka
# - .\mongodb_consumer_kafka
# - .\sensor_logger_fast_api_kafka

$images = @(
    "cpu_logger_kafka",
    "mongodb_consumer_kafka",
    "sensor_logger_fast_api_kafka"
)

foreach ($image in $images) {
    Write-Host "Building image $image"
    docker build -t $image .\$image
}