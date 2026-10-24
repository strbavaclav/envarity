from datetime import date

import yaml


def parse_image_dates(yaml_text: str) -> dict[str, date]:
    data = yaml.safe_load(yaml_text)
    return {image: date.fromisoformat(value) for image, value in data.items()}


def days_behind(
    all_versions: dict[str, dict[str, date]],
) -> dict[str, dict[str, int | None]]:
    newest: dict[str, date] = {}
    for dates_by_image in all_versions.values():
        for image, d in dates_by_image.items():
            if image not in newest or d > newest[image]:
                newest[image] = d

    result: dict[str, dict[str, int | None]] = {}
    for branch, dates_by_image in all_versions.items():
        result[branch] = {}
        for image, newest_date in newest.items():
            if image in dates_by_image:
                result[branch][image] = (newest_date - dates_by_image[image]).days
            else:
                result[branch][image] = None  # missing entirely
    return result
