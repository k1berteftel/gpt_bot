

prices = {
    'image': {
        'text': 12,
        'combo': 41
    },
    'video': {
        'kling': 121,
        'seedance': {
            'lite': 61,
            'pro': 81
        }
    },
    'task': 11
}


duration_prices = {
    'seedance_lite': {
        5: 61,
        10: 101
    },
    'seendance_pro': {
        5: 81,
        10: 131,
    },
    'kling': {
        5: 121,
        10: 242,
    }
}

model_ratios = {
    'seedance': ["16:9", "9:16"],
    'kling': ["16:9", "9:16"]
}


def get_video_price(data: dict):
    model = data.get('model')
    sub_model = data.get('sub_model')
    params = data.get('params')
    model_name = model
    if model in ['seedance']:
        model_name = model + '_' + sub_model
    price = duration_prices[model_name].get(params.get('duration'))
    return price