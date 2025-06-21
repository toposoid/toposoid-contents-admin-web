# toposoid-contents-admin-web
This is a WEB API that works as a microservice within the Toposoid project.
Toposoid is a knowledge base construction platform.(see [Toposoid　Root Project](https://github.com/toposoid/toposoid.git))
This microservice is responsible for managing content. Specifically, this includes image management. outputs the result in JSON.

[![Test And Build](https://github.com/toposoid/toposoid-contents-admin-web/actions/workflows/action.yml/badge.svg)](https://github.com/toposoid/toposoid-contents-admin-web/actions/workflows/action.yml)

<img width="1154"  src="https://github.com/toposoid/toposoid-contents-admin-web/assets/82787843/eb464f57-2129-4e39-abbc-de0f4837aad9">

## Dependency in toposoid Project

## Requirements
* Docker version 20.10.x, or later
* docker-compose version 1.22.x

## Recommended Environment For Standalone
* Required: at least 1.61G of HDD(Docker Image Size)

## Setup For Standalone
```bssh
docker-compose up
```
The first startup takes a long time until docker pull finishes.
## Usage
* This API reads the image of the URL, processes the image, and returns the URL managed by Toposoid.
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "id": "d64f48da-0efb-4bf8-b1d4-75a5fa7cec72",
    "imageReference":{
    "reference": {
        "url": "",
        "surface": "猫が",
        "surfaceIndex": "0",
        "isWholeSentence": false,
        "originalUrlOrReference": "http://images.cocodataset.org/val2017/000000039769.jpg"
    },
    "x": 27,
    "y": 41,
    "width": 287,
    "height": 435}
}' http://localhost:9012/registImage
```
* if you want to upload temporary content, please use uploadTemporaryImage Action.

## Note
* This microservice uses 9012 as the default port.

## License
This program is offered under a commercial and under the AGPL license.
For commercial licensing, contact us at https://toposoid.com/contact.  
For AGPL licensing, see below.

AGPL licensing:
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Author
* Makoto Kubodera([Linked Ideal LLC.](https://linked-ideal.com/))

Thank you!

