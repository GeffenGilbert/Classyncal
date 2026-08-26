import { useState } from "react";

// Returns item indices sorted chronologically by date (then time as a
// tiebreaker), so callers can render in sorted order while still using the
// original index for onUpdate/onRemove — the underlying array itself is
// left untouched.
//
// `indices` optionally restricts the result to a subset of `items`, which is
// how a tab renders one category (e.g. only tasks whose task_type is project)
// while still addressing the full array by its real indices.
export function getSortedIndices(items, dateField, timeField, indices) {
  return (indices ?? items.map((_, index) => index))
    .slice()
    .sort((a, b) => {
      const dateA = items[a][dateField];
      const dateB = items[b][dateField];
      if (dateA !== dateB) {
        if (!dateA) return 1;
        if (!dateB) return -1;
        return dateA < dateB ? -1 : 1;
      }

      const timeA = items[a][timeField];
      const timeB = items[b][timeField];
      if (timeA === timeB) return 0;
      if (!timeA) return -1;
      if (!timeB) return 1;
      return timeA < timeB ? -1 : 1;
    });
}

// Sorts once, the moment a tab is first shown, then holds that order fixed -
// otherwise clearing an item's date (e.g. to fix a validation error) would
// instantly resort it to the bottom of the list, out from under the user
// mid-edit. Removed items drop out on their own since they're no longer in
// `indices`; items added afterward have no date to place them by, so they're
// appended in the order they were added.
export function useFrozenSortedIndices(items, dateField, timeField, indices) {
  const [orderedKeys] = useState(() =>
    getSortedIndices(items, dateField, timeField, indices).map((index) => items[index]._key),
  );

  const currentIndexByKey = new Map(indices.map((index) => [items[index]._key, index]));
  const knownKeys = new Set(orderedKeys);

  return [
    ...orderedKeys.filter((key) => currentIndexByKey.has(key)).map((key) => currentIndexByKey.get(key)),
    ...indices.filter((index) => !knownKeys.has(items[index]._key)),
  ];
}
