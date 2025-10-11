

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


model_examples = {
    'image': {
        'text': {
            'text': '<b>Промпт:</b>\n<blockquote expandable>Летающий остров в форме черепахи с замком на спине, '
                    'парящий в фиолетовом небе</blockquote>',
            'media': 'media/image_gen/text_img.jpg',
            'media_type': 'photo',
            'url': 'https://t.me/pakrnet'
        },
        'combo': {
            'text': '<b>Промпт:</b>\n<blockquote expandable>Создайте сцену в галерее современного искусства, '
                    'используя прилагаемое изображение лица и внешности девушки, не меняя её черты лица. '
                    'На стене висит большой портрет девушки маслом. Её лицо и верхняя часть тела написаны в '
                    'реалистичной, экспрессивной манере масляной живописи с текстурированными мазками и '
                    'приглушенными цветами.\nЧистая красная стена галереи создает профессиональную атмосферу выставки '
                    'благодаря мягкому освещению, освещающему произведение искусства.\nПеред картиной в тёмно-зелёном '
                    'кресле, видимом сзади, сидит её бывший парень, держа в руке сигарету, из которой поднимается '
                    'тонкий дымок, что придаёт сцене кинематографическое и таинственное настроение</blockquote>',
            'media': 'media/image_gen/text+photo_img.jpg',
            'media_type': 'photo',
            'url': 'https://t.me/pakrnet'
        },
    },
    'video':  {
        'kling': {
            'text': '<b>Промпт:</b>\n<blockquote expandable>The setting has warm lighting from streetlights or '
                    'soft party lights. A little boy around 2 to 3 years old, with light skin tone, broun hair, '
                    'and big green expressive eyes, runs joyfully toward a young couple sitting close together. '
                    'The couple must look exactly like the people in the attached photo — no changes to their facial '
                    'features, skin tone, hairstyle, or clothing. They both have medium skin, man have dark hair, '
                    'women have broun hair and are man wearing summer outfits. The child should clearly look like '
                    'the boy, with features that naturally combine both parents. He hugs them lovingly, wrapping her '
                    'arms around them, smiling and laughing. The couple smiles and embraces he warmly. The video '
                    'should feel authentic, as if casually filmed by a friend or family member on a phone — slightly '
                    'shaky, casually composed, and emotionally genuine</blockquote>',
            'media_type': 'video',
            'media': 'media/video_gen/kling.MP4',
            'url': 'https://t.me/pakrnet'
        },
        'seedance': {
            'lite': {
                'text': '<b>Промпт:</b>\n<blockquote expandable> Семья улыбается и машет рукой</blockquote>',
                'media': 'media/video_gen/seedance_video.mp4',
                'media_type': 'video',
                'url': 'https://t.me/pakrnet'
            },
            'pro': {
                'text': '<b>Промпт:</b>\n<blockquote expandable> Семья улыбается и машет рукой</blockquote>',
                'media': 'media/video_gen/seedance_video.mp4',
                'media_type': 'video',
                'url': 'https://t.me/pakrnet'
            }
        }
    }
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