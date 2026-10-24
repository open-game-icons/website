// Call Prettier's API directly because its CLI can't resolve `npm:` plugin
// specifiers when run through Deno. Versions are pinned here; the dprint exec
// config invalidates its cache when this file changes.
import * as jinjaPlugin from "npm:prettier-plugin-jinja-template@2.2.0";
import * as prettierHtml from "npm:prettier@3.9.9/plugins/html";
import * as prettier from "npm:prettier@3.9.9/standalone";

const [printWidth = "120", tabWidth = "2", useTabs = "false"] = Deno.args;
const input = await new Response(Deno.stdin.readable).text();

const output = await prettier.format(input, {
  parser: "jinja-template",
  plugins: [prettierHtml, jinjaPlugin],
  printWidth: Number(printWidth),
  tabWidth: Number(tabWidth),
  useTabs: useTabs === "true",
  bracketSameLine: true,
});

await Deno.stdout.write(new TextEncoder().encode(output));
