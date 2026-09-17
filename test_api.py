from src.skin_api import HD_ACTIONS, SD_ACTIONS, output_items


def test_action_sets():
    assert all(x.startswith("hd_") for x in HD_ACTIONS)
    assert all(not x.startswith("hd_") for x in SD_ACTIONS)


def test_output_parser():
    payload = {
        "data": {
            "task_status": "success",
            "results": {
                "output": [
                    {
                        "type": "texture",
                        "ui_score": 68,
                        "raw_score": 57.33,
                        "mask_urls": ["https://example.com/mask.png"],
                    }
                ]
            }
        }
    }
    items = output_items(payload)
    assert len(items) == 1
    assert items[0]["ui_score"] == 68
