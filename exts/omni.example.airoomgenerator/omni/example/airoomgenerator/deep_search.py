# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from omni.kit.ngsearch.client import NGSearchClient
import asyncio
import carb
import requests

def _process_json_data(json_data):
    """Process the JSON data returned by USD Search API."""
    for item in json_data:
        # replace search server with content server
        item["url"] = item["url"].replace(
            "s3://deepsearch-demo-content/",
            "https://omniverse-content-production.s3.us-west-2.amazonaws.com/"
        )
        # optionally store images in temp location
        """
        import base64
        import tempfile
        if "image" in item:
            # Create a temporary file in the system's temp directory
            with tempfile.NamedTemporaryFile(prefix="temp_", suffix=".png", delete=False) as temp_file:
                # Decode the base64 image data and write it to the temp file
                image_data = base64.b64decode(item["image"])
                temp_file.write(image_data)
                full_path = temp_file.name

            # Replace the base64 encoded image with the file path
            item["image"] = full_path

            if "bbox_dimension_x" in item:
                item["bbox_dimension"] = [
                    item["bbox_dimension_x"],
                    item["bbox_dimension_y"],
                    item["bbox_dimension_z"],
                ]
        """

        return json_data

async def send_api_request(query):
    import os

    _url = "http://10.0.10.4:30517/v2/deepsearch/search"

    _api_key = "b21uaXZlcnNlOjNMOXVYcFQ2I053IXFGNXZSMXNAa0U4alkyYlc3eg=="

    _payload = {
        "description": query,
        "limit": 1,
        "cutoff_threshold": 1.05,
        "return_images": False,
        "return_metadata": False,
        "return_root_prims": False,
        "return_predictions": False,
        "file_extension_include": "usd",
    }

    _headers = {
        "Authorization": "Basic {}".format(_api_key),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        # Send the GET request
        _response = requests.post(_url, headers=_headers, json=_payload)
        _response.raise_for_status()

        result = _response.json()
        # Process the JSON data
        filtered_result = _process_json_data(result)
        return filtered_result
    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}

async def query_items(queries, url: str, paths):

    result = list(tuple())        
    for query in queries:
        query_result = await _query_first(query, url, paths)

        if query_result is not None:
            result.append(query_result)
        
    return result

async def _query_first(query: str, url: str, paths):

    filtered_query = "ext:usd,usdz,usda "

    if len(paths) > 0:
        filtered_query = filtered_query + " path: "

        for path in paths:
            filtered_query = filtered_query + "\"" + str(path) + "\","
        
        filtered_query = filtered_query[:-1]
    
        filtered_query = filtered_query + " "

    filtered_query = filtered_query + query

    search_result = await send_api_request(query)
    
    if search_result is not None:
        if isinstance(search_result, list) and len(search_result) > 0:
            return (query, search_result[0]["url"])
    else:
        carb.log_warn(f"Search Results came up with nothing for {query}. Make sure you've configured your nucleus path")
    return None
    
async def query_all(query: str, url: str, paths):

    filtered_query = "ext:usd,usdz,usda " + query
    # return await NGSearchClient.get_instance().find2(query=filtered_query, url=url)
    if len(paths) > 0:
        filtered_query = filtered_query + " path: "

        for path in paths:
            filtered_query = filtered_query + "\"" + str(path) + "\","
        
        filtered_query = filtered_query[:-1]
    
        filtered_query = filtered_query + " "

    filtered_query = filtered_query + query

    return await send_api_request(filtered_query)
        
