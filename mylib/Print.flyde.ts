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
