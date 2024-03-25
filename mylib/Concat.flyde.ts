import { CodeNode } from "@flyde/core";

export const Concat: CodeNode = {
  id: "Concat",
  description: "Concatenate two strings",
  inputs: { a: { description: "First string" }, b: { description: "Second string" } },
  outputs: { out: { description: "Concatenated string" } },
  run: ({ msg }) => {
    console.log(msg);
  },
};
