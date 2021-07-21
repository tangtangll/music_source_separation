import argparse
import os
import pickle

import h5py

from music_source_separation.utils import read_yaml


def create_indexes(args):
    r"""Create and write out training indexes into disk. In training a source
    separation system, training indexes will be shuffled and iterated for
    selecting segments to be mixed. E.g., the training indexes_dict looks like:

        {'vocals': [
             [./piece1.h5, 0, 132300],
             [./piece1.h5, 4410, 136710],
             [./piece1.h5, 8820, 141120],
             ...
         ],
         'accompaniment': [
             [./piece1.h5, 0, 132300],
             [./piece1.h5, 4410, 136710],
             [./piece1.h5, 8820, 141120],
             ...
         ]
        }
    """
    # Arugments & parameters
    workspace = args.workspace
    config_yaml = args.config_yaml

    # Only create indexes for training, because evalution is on entire pieces.
    split = "train"

    # Read config file.
    configs = read_yaml(config_yaml)

    sample_rate = configs["sample_rate"]
    segment_samples = int(configs["segment_seconds"] * sample_rate)

    # Path to write out index.
    indexes_path = os.path.join(workspace, configs[split]["indexes"])
    os.makedirs(os.path.dirname(indexes_path), exist_ok=True)

    source_types = configs[split]["source_types"].keys()
    # E.g., ['vocals', 'accompaniment']

    indexes_dict = {source_type: [] for source_type in source_types}
    # E.g., indexes_dict will looks like: {
    #     'vocals': [
    #         [./piece1.h5, 0, 132300],
    #         [./piece1.h5, 4410, 136710],
    #         [./piece1.h5, 8820, 141120],
    #         ...
    #     ],
    #     'accompaniment': [
    #         [./piece1.h5, 0, 132300],
    #         [./piece1.h5, 4410, 136710],
    #         [./piece1.h5, 8820, 141120],
    #         ...
    #     ]
    # }

    # tmp_dict = {source_type: {} for source_type in source_types}

    # Get training indexes for each source type.
    for source_type in source_types:

        print("--- {} ---".format(source_type))

        dataset_types = configs[split]["source_types"][source_type]
        # E.g., ['musdb18', ...]

        # Each source can come from mulitple datasets.
        for dataset_type in dataset_types:

            hdf5s_dir = os.path.join(
                workspace, dataset_types[dataset_type]["directory"]
            )
            hop_samples = int(dataset_types[dataset_type]["hop_seconds"] * sample_rate)

            hdf5_names = sorted(os.listdir(hdf5s_dir))
            print("Hdf5 files num: {}".format(len(hdf5_names)))

            # Traverse all packed hdf5 files of a dataset.
            for n, hdf5_name in enumerate(hdf5_names):

                print(n, hdf5_name)
                hdf5_path = os.path.join(hdf5s_dir, hdf5_name)

                with h5py.File(hdf5_path, "r") as hf:

                    start_sample = 0
                    while start_sample + segment_samples < hf[source_type].shape[-1]:
                        indexes_dict[source_type].append(
                            [hdf5_path, start_sample, start_sample + segment_samples]
                        )

                        start_sample += hop_samples

                    # If the audio length is shorter than the segment length, 
                    # then use the audio as a segment.
                    if start_sample == 0:
                        indexes_dict[source_type].append(
                            [hdf5_path, start_sample, start_sample + segment_samples]
                        )

        print(
            "Total indexes for {}: {}".format(
                source_type, len(indexes_dict[source_type])
            )
        )

    pickle.dump(indexes_dict, open(indexes_path, "wb"))
    print("Write index dict to {}".format(indexes_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode")

    # Create training indexes.
    parser_create_indexes = subparsers.add_parser("create_indexes")
    parser_create_indexes.add_argument(
        "--workspace", type=str, required=True, help="Directory of workspace."
    )
    parser_create_indexes.add_argument(
        "--config_yaml", type=str, required=True, help="User defined config file."
    )

    # Parse arguments.
    args = parser.parse_args()

    if args.mode == "create_indexes":
        create_indexes(args)

    else:
        raise Exception("Incorrect arguments!")