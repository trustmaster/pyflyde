import { CodeNode } from "@flyde/core";

export const Print: CodeNode = {
  id: "Print",
  description: "Prints the input message to the console.",
  inputs: { 
    msg: {"description": "The message to print"}
 },
  outputs: {  },
  run: () => { return; },
};

export const Concat: CodeNode = {
  id: "Concat",
  description: "Concatenates two strings.",
  inputs: { 
    a: {"description": "The first string"},
    b: {"description": "The second string"}
 },
  outputs: { 
    out: {"description": "The concatenated string"}
 },
  run: () => { return; },
};

