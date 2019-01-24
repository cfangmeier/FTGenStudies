import dill
import argparse

def main(inputs):
    print(inputs)
    output = {}
    for input in inputs:
        with open(input) as f:
            output.update(dill.load(f))
    with open('output.dill', 'w') as f:
        dill.dump(output, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputs', nargs='+')
    args = parser.parse_args()
    main(args.inputs)
