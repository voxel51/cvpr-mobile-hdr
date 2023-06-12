import argparse
from pathlib import Path

import fiftyone as fo


def get_sample_tags(sample_filepath: Path):
    path_tokens = sample_filepath.parts
    is_train = "training_npz" in path_tokens
    is_dynamic = is_train and "dynamic" in path_tokens
    is_static = is_train and "static_translate" in path_tokens
    is_white_balanced = sample_filepath.name[: -len(".npz")].endswith("wb_grayworld")

    sample_tags = []
    if is_train:
        sample_tags.append("train")
    else:
        sample_tags.append("test")

    if is_dynamic:
        sample_tags.append("dynamic")

    if is_static:
        sample_tags.append("static_translate")

    if is_white_balanced:
        sample_tags.append("white_balanced")

    return sample_tags


def add_samples_for_split(dataset: fo.Dataset, split: list[Path]):
    for hdr_sample_path in split:
        group = fo.Group()
        photo_id = hdr_sample_path.name.split("_")[0]

        common_sample_tags = get_sample_tags(hdr_sample_path)
        is_white_balanced = "white_balanced" in common_sample_tags

        hdr_sample = fo.Sample(
            filepath=str(hdr_sample_path.absolute()),
            tags=[*common_sample_tags, "hdr", "ground_truth"],
            group=group.element("hdr"),
        )
        hdr_sample["exposure"] = "hdr"
        hdr_sample["white_balanced"] = (
            "white_balanced" if is_white_balanced else "no_white_balance"
        )
        hdr_sample["photo_id"] = photo_id

        sht_sample_path = (
            hdr_sample_path.parent.parent / "sht" / hdr_sample_path.name
        ).absolute()
        sht_sample = fo.Sample(
            filepath=str(sht_sample_path),
            tags=[*common_sample_tags, "sht"],
            group=group.element("sht"),
        )
        sht_sample["exposure"] = "sht"
        sht_sample["white_balanced"] = (
            "white_balanced" if is_white_balanced else "no_white_balance"
        )
        sht_sample["photo_id"] = photo_id

        mid_sample_path = (
            hdr_sample_path.parent.parent / "mid" / hdr_sample_path.name
        ).absolute()
        mid_sample = fo.Sample(
            filepath=str(mid_sample_path),
            tags=[*common_sample_tags, "mid"],
            group=group.element("mid"),
        )
        mid_sample["exposure"] = "mid"
        mid_sample["white_balanced"] = (
            "white_balanced" if is_white_balanced else "no_white_balance"
        )
        mid_sample["photo_id"] = photo_id

        lng_sample_path = (
            hdr_sample_path.parent.parent / "lng" / hdr_sample_path.name
        ).absolute()
        lng_sample = fo.Sample(
            filepath=str(lng_sample_path),
            tags=[*common_sample_tags, "lng"],
            group=group.element("lng"),
        )
        lng_sample["exposure"] = "lng"
        lng_sample["white_balanced"] = (
            "white_balanced" if is_white_balanced else "no_white_balance"
        )
        lng_sample["photo_id"] = photo_id

        dataset.add_samples(
            [hdr_sample, sht_sample, mid_sample, lng_sample],
        )


def add_samples(dataset: fo.Dataset, data_root_dir: str):
    training_dynamic_hdr = list(
        Path(f"{data_root_dir}/training_npz/dynamic/hdr").glob("**/*.[pPjJ][nNpP][gG]")
    )
    training_static_hdr = list(
        Path(f"{data_root_dir}/training_npz/static_translate/hdr").glob(
            "**/*.[pPjJ][nNpP][gG]"
        )
    )
    test_with_gt_hdr = list(
        Path(f"{data_root_dir}/test_npz/test_withGT/hdr").glob("**/*.[pPjJ][nNpP][gG]")
    )

    add_samples_for_split(dataset, training_dynamic_hdr)
    add_samples_for_split(dataset, training_static_hdr)
    add_samples_for_split(dataset, test_with_gt_hdr)


def create_dataset_and_add_samples(dataset_name: str, data_root_dir: str):
    print(f"creating dataset {dataset_name}")
    dataset = fo.Dataset(name=dataset_name)
    dataset.persistent = True

    add_samples(dataset, data_root_dir)
    dataset.save()

    return dataset


def main(dataset_name: str, data_root_dir: str, launch_app: bool, reimport: bool):
    # check if dataset exists
    if dataset_name in fo.list_datasets():
        if reimport:
            print("deleting existing dataset")
            fo.delete_dataset(dataset_name)

            dataset = create_dataset_and_add_samples(dataset_name, data_root_dir)
        else:
            print(
                f"using existing dataset {dataset_name}. skipping files import. use --reimport to reimport"
            )
            dataset = fo.load_dataset(dataset_name)
    else:
        dataset = create_dataset_and_add_samples(dataset_name, data_root_dir)

    print(f"dataset {dataset_name} available with {len(dataset)} samples")

    if launch_app:
        print("launching app")
        session = fo.launch_app(dataset, remote=True, auto=False)
        session.wait(-1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fiftyone Importer")

    parser.add_argument(
        "--dataset_name",
        help="Name of the dataset",
        default="Mobile-HDR",
    )

    parser.add_argument(
        "--data_root_dir",
        help="Root directory of PNG/JPG files. Should contain training_npz and test_npz",
        default="Mobile-HDR/JPG_data",
    )

    parser.add_argument(
        "--launch_app",
        help="Whether to launch the app",
        default=True,
        action="store_true",
    )

    parser.add_argument(
        "--reimport",
        help="Whether to delete existing import and reimport",
        default=False,
        action="store_true",
    )

    args, unknown_args = parser.parse_known_args()

    if unknown_args:
        print(f"unknown args: {unknown_args}")
        exit(1)

    main(args.dataset_name, args.data_root_dir, args.launch_app, args.reimport)
