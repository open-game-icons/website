function main(): void {
  const element = document.getElementById("build-time");
  if (!(element instanceof HTMLTimeElement)) return;

  const date = new Date(element.dateTime);
  if (Number.isNaN(date.getTime())) return;

  element.textContent = date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

main();

export {};
