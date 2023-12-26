import random
import math
import json

DEFAULT_CONTAINERS_NUM = 1
DEFAULT_MEAN_CONTAINER_WIDTH = 50
DEFAULT_MEAN_CONTAINER_LENGTH = 50
DEFAULT_ITEMS_NUM = 30
DEFAULT_MEAN_ITEM_WIDTH = 5
DEFAULT_MEAN_ITEM_LENGTH = 3


def generate_problem_data(**kwargs):
    """
    Function for generating problem data according to provided guidelines.

    KEYWORD PARAMETERS
        containers_num : number of containers (default 1)
        containers_length : average containers length (default 50)
        containers_width : average containers width (default 50)
        items_num: number of items per container (default 30)
        items_length: average length of items (default 5)
        items_width: average width of items (default 5)
    """
    # ---------------------- CONTAINERS ------------------------
    containers_num = kwargs.get("containers_num", DEFAULT_CONTAINERS_NUM)
    container_length = kwargs.get("containers_length", DEFAULT_MEAN_CONTAINER_LENGTH)
    container_width = kwargs.get("containers_width", DEFAULT_MEAN_CONTAINER_WIDTH)

    deviation_W_val = round(container_width * 0.1)
    deviation_H_val = round(container_length * 0.1)

    lower_W_val, upper_W_val = (
        container_width - deviation_W_val,
        container_width + deviation_W_val,
    )
    lower_H_val, upper_H_val = (
        container_length - deviation_H_val,
        container_length + deviation_H_val,
    )

    containers = {}
    for cont_num in range(containers_num):
        containers[f"container-{cont_num}"] = {
            "W": random.randint(lower_W_val, upper_W_val),
            "L": random.randint(lower_H_val, upper_H_val),
        }

    # ---------------------- ITEMS ------------------------
    items_num = kwargs.get("items_num", DEFAULT_ITEMS_NUM)
    items_length = kwargs.get("items_length", DEFAULT_MEAN_ITEM_LENGTH)
    items_width = kwargs.get("items_width", DEFAULT_MEAN_ITEM_WIDTH)

    deviation_w_val = max(round(items_length * 0.6), 1)
    deviation_h_val = max(round(items_width * 0.6), 1)

    lower_w_val, upper_w_val = (
        items_width - deviation_w_val,
        items_width + deviation_w_val,
    )
    lower_h_val, upper_h_val = (
        items_width - deviation_h_val,
        items_width + deviation_h_val,
    )
    items = {}
    total_items_num = items_num * containers_num
    for item_num in range(total_items_num):
        items[f"item-{item_num}"] = {
            "w": random.randint(lower_w_val, upper_w_val),
            "l": random.randint(lower_h_val, upper_h_val),
        }

    print("Containers number = ", containers_num)
    print("Containers:")
    print(json.dumps(containers, indent=4))
    print("Items number = ", len(items))

    return {"containers": containers, "items": items}
