import { CodeNode } from "@flyde/core";

export const Print: CodeNode = {
  id: "Print",
  description: "Prints the incoming messages",
  inputs: { msg: { description: "Message to be printed"} },
  outputs: {},
  run: ({ msg }) => {
    console.log(msg);
  },
};

export const Concat: CodeNode = {
  id: "Concat",
  description: "Concatenate two strings",
  inputs: { a: { description: "First string" }, b: { description: "Second string" } },
  outputs: { out: { description: "Concatenated string" } },
  run: ({ msg }) => {
    console.log(msg);
  },
};
