// Drive a real librime session from a script on stdin.
//
//   drive <shared_data_dir> <user_data_dir> <schema_id> [--deploy]
//
// Each input line is one of:
//   q<TAB>keys<TAB>expected   rank of expected among candidates, plus preedit and top candidate
//   c<TAB>keys                type keys, press space, report whether it was accepted and the commit
//   s<TAB>keys<TAB>option     as c, with the named option switched on and then off again
//
// A rank of 0 means expected was not among the first MAX_CANDIDATES candidates.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <rime_api.h>

enum { MAX_CANDIDATES = 200 };

static const char* field(char** cursor) {
  char* start = *cursor;
  if (!start)
    return "";
  char* tab = strchr(start, '\t');
  if (tab) {
    *tab = '\0';
    *cursor = tab + 1;
  } else {
    *cursor = NULL;
  }
  return start;
}

static void type_keys(RimeApi* rime, RimeSessionId session, const char* keys) {
  for (const char* p = keys; *p; ++p)
    rime->process_key(session, (unsigned char)*p, 0);
}

static void query(RimeApi* rime, RimeSessionId session, const char* keys, const char* expected) {
  type_keys(rime, session, keys);
  RIME_STRUCT(RimeContext, ctx);
  const char* preedit = "";
  if (rime->get_context(session, &ctx) && ctx.composition.preedit)
    preedit = ctx.composition.preedit;
  char top[256] = "";
  int rank = 0;
  RimeCandidateListIterator it = {0};
  if (rime->candidate_list_begin(session, &it)) {
    int seen = 0;
    while (seen < MAX_CANDIDATES && rime->candidate_list_next(&it)) {
      ++seen;
      if (seen == 1)
        snprintf(top, sizeof top, "%s", it.candidate.text);
      if (!rank && strcmp(it.candidate.text, expected) == 0)
        rank = seen;
    }
    rime->candidate_list_end(&it);
  }
  printf("%s\t%s\t%d\t%s\t%s\n", keys, expected, rank, preedit, top);
  rime->free_context(&ctx);
  rime->clear_composition(session);
}

static void commit(RimeApi* rime, RimeSessionId session, const char* keys) {
  type_keys(rime, session, keys);
  Bool accepted = rime->process_key(session, ' ', 0);
  RIME_STRUCT(RimeCommit, out);
  const char* text = "";
  if (rime->get_commit(session, &out) && out.text)
    text = out.text;
  printf("%s\taccepted=%d\t%s\n", keys, accepted ? 1 : 0, text);
  rime->free_commit(&out);
  rime->clear_composition(session);
}

int main(int argc, char** argv) {
  if (argc < 4) {
    fprintf(stderr, "usage: %s shared user schema [--deploy]\n", argv[0]);
    return 2;
  }
  RimeApi* rime = rime_get_api();
  RIME_STRUCT(RimeTraits, traits);
  traits.shared_data_dir = argv[1];
  traits.user_data_dir = argv[2];
  traits.distribution_name = "rime-bayan tests";
  traits.distribution_code_name = "rime-bayan-tests";
  traits.distribution_version = "0";
  traits.app_name = "rime.bayan_tests";
  traits.min_log_level = 2;
  rime->setup(&traits);
  rime->initialize(&traits);
  if (argc > 4 && strcmp(argv[4], "--deploy") == 0) {
    rime->start_maintenance(True);
    rime->join_maintenance_thread();
  }
  RimeSessionId session = rime->create_session();
  if (!session || !rime->select_schema(session, argv[3])) {
    fprintf(stderr, "cannot select schema %s\n", argv[3]);
    return 1;
  }
  char schema[64] = "";
  rime->get_current_schema(session, schema, sizeof schema);
  if (strcmp(schema, argv[3]) != 0) {
    fprintf(stderr, "session is on %s, wanted %s\n", schema, argv[3]);
    return 1;
  }
  char line[4096];
  while (fgets(line, sizeof line, stdin)) {
    line[strcspn(line, "\r\n")] = '\0';
    char* cursor = line;
    const char* verb = field(&cursor);
    const char* keys = field(&cursor);
    const char* arg = field(&cursor);
    if (strcmp(verb, "q") == 0) {
      query(rime, session, keys, arg);
    } else if (strcmp(verb, "c") == 0) {
      commit(rime, session, keys);
    } else if (strcmp(verb, "s") == 0) {
      rime->set_option(session, arg, True);
      commit(rime, session, keys);
      rime->set_option(session, arg, False);
    }
  }
  rime->destroy_session(session);
  rime->finalize();
  return 0;
}
