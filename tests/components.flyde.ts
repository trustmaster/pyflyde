import { CodeNode } from "@flyde/core";

export const Format: CodeNode = {
  id: "Format",
  description: "Formats the input value with a given format string and sends it to out.",
  inputs: {
    inp: { description: "The input" },
    format: { description: "The format string" }
  },
  outputs: {
    out: { description: "The formatted output" }
  },
  run: () => { return; },
};

export const Echo: CodeNode = {
  id: "Echo",
  description: "A simple component that echoes the input.",
  inputs: {
    inp: { description: "The input" }
  },
  outputs: {
    out: { description: "The output" }
  },
  run: () => { return; },
};

export const Capitalize: CodeNode = {
  id: "Capitalize",
  description: "A component that capitalizes the input.",
  inputs: {
    inp: { description: "The input" }
  },
  outputs: {
    out: { description: "The output" }
  },
  run: () => { return; },
};

export const RepeatWordNTimes: CodeNode = {
  id: "RepeatWordNTimes",
  description: "A component that has both inputs and outputs and a sticky input.",
  inputs: {
    word: { description: "The input" },
    times: { description: "The number of times to repeat the input" }
  },
  outputs: {
    out: { description: "The output" }
  },
  run: () => { return; },
};

