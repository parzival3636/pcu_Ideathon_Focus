// MindForge — Feature Extraction for ML Classifier
// Extracts TF-IDF-like feature vectors from page content for classification.
// Runs in the service worker (background.js context).

import { buildVocabulary, TRAINING_DATA } from './trainingData.js';

let _vocabulary = null;
let _vocabIndex = null; // token → index mapping

/**
 * Initialize vocabulary from training data.
 * Called once on extension start.
 */
export function initFeatures() {
  _vocabulary = buildVocabulary();
  _vocabIndex = {};
  _vocabulary.forEach((token, i) => { _vocabIndex[token] = i; });
  console.log(`[MindForge ML] Vocabulary initialized: ${_vocabulary.length} terms`);
  return _vocabulary;
}

/**
 * Tokenize text into cleaned unigrams and bigrams.
 */
function tokenize(text) {
  if (!text) return [];
  const words = text.toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2);

  const tokens = [...words];

  // Add bigrams
  for (let i = 0; i < words.length - 1; i++) {
    tokens.push(words[i] + ' ' + words[i + 1]);
  }

  return tokens;
}

/**
 * Build a sparse TF vector from text against the vocabulary.
 * Returns a Float64Array of term frequencies (normalized).
 */
function buildTFVector(text) {
  if (!_vocabulary) initFeatures();

  const tokens = tokenize(text);
  const vec = new Float64Array(_vocabulary.length + META_FEATURES_COUNT);

  if (tokens.length === 0) return vec;

  // Count term frequencies
  for (const token of tokens) {
    const idx = _vocabIndex[token];
    if (idx !== undefined) {
      vec[idx]++;
    }
  }

  // Normalize by document length (TF normalization)
  const maxTF = Math.max(1, ...vec.slice(0, _vocabulary.length));
  for (let i = 0; i < _vocabulary.length; i++) {
    vec[i] = vec[i] / maxTF;
  }

  return vec;
}

// ─── Meta Features ───
// Additional non-text features appended to the vector
const META_FEATURES_COUNT = 10;

/**
 * Detect content type from extracted content signals.
 */
export function detectContentType(extractedContent) {
  const content = (extractedContent.content || '').toLowerCase();
  const title = (extractedContent.title || '').toLowerCase();
  const url = (extractedContent.url || '').toLowerCase();
  const allText = title + ' ' + content + ' ' + url;

  // Video signals
  const videoSignals = ['video', 'watch', 'stream', 'episode', 'movie', 'film',
    'lecture video', 'tutorial video', 'youtube.com/watch', 'vimeo.com',
    'twitch.tv', 'netflix.com', 'mp4', 'webm'];
  const videoScore = videoSignals.reduce((s, sig) => s + (allText.includes(sig) ? 1 : 0), 0);

  // Audio signals
  const audioSignals = ['podcast', 'audio', 'listen', 'spotify', 'music',
    'soundcloud', 'mp3', 'radio', 'beats', 'lofi', 'song', 'album'];
  const audioScore = audioSignals.reduce((s, sig) => s + (allText.includes(sig) ? 1 : 0), 0);

  // Interactive signals (coding, quizzes, tools)
  const interactiveSignals = ['editor', 'compiler', 'playground', 'sandbox',
    'quiz', 'exercise', 'practice', 'challenge', 'interactive', 'colab',
    'replit', 'codepen', 'jsfiddle', 'leetcode', 'hackerrank', 'codeforces'];
  const interactiveScore = interactiveSignals.reduce((s, sig) => s + (allText.includes(sig) ? 1 : 0), 0);

  if (interactiveScore > videoScore && interactiveScore > audioScore && interactiveScore >= 1) return 'interactive';
  if (videoScore > audioScore && videoScore >= 1) return 'video';
  if (audioScore >= 2) return 'audio';
  return 'text';
}

/**
 * Compute goal similarity between session goal and page content.
 * Returns a score 0-1.
 */
export function computeGoalSimilarity(goalText, pageText) {
  if (!goalText || !pageText) return 0;

  const goalTokens = new Set(tokenize(goalText));
  const pageTokens = new Set(tokenize(pageText));

  if (goalTokens.size === 0) return 0;

  let matches = 0;
  for (const token of goalTokens) {
    if (pageTokens.has(token)) matches++;
  }

  return matches / goalTokens.size;
}

// ─── Abbreviation / Synonym Expansion Map ───
// Maps common short session goal names to their full forms and related keywords.
// This allows "toc" to match content about "theory of computation", "DFD", etc.
const GOAL_EXPANSIONS = {
  // Theory of Computation
  'toc': 'theory of computation automata formal languages grammar turing machine dfa nfa dfd pushdown regular expression context free chomsky pumping lemma decidability complexity finite state computability',
  'theory of computation': 'toc automata formal languages grammar turing machine dfa nfa dfd pushdown regular expression context free chomsky pumping lemma decidability',

  // Data Structures & Algorithms
  'dsa': 'data structures algorithms arrays linked list tree graph stack queue heap hash table sorting searching dynamic programming greedy recursion binary search',
  'data structures': 'dsa algorithms arrays linked list tree graph stack queue heap hash table sorting binary search',
  'algorithms': 'dsa data structures sorting searching dynamic programming greedy recursion complexity analysis',

  // Operating Systems
  'os': 'operating system operating systems processes threads scheduling memory management kernel deadlock paging virtual memory file system semaphore mutex process synchronization',
  'operating system': 'os processes threads scheduling memory management kernel deadlock paging virtual memory semaphore',
  'operating systems': 'os processes threads scheduling memory management kernel deadlock paging virtual memory semaphore',

  // Database Management Systems
  'dbms': 'database management system sql normalization relational algebra transaction query optimization indexing er diagram entity relationship schema',
  'database': 'dbms sql normalization relational transaction query indexing schema entity relationship',
  'sql': 'database dbms query relational table join select insert update normalization',

  // Computer Networks
  'cn': 'computer networks networking tcp udp ip osi model routing protocol http dns socket subnet gateway firewall layer transport network',
  'computer networks': 'cn networking tcp udp ip osi model routing protocol http dns socket subnet',
  'networking': 'cn computer networks tcp udp ip osi routing protocol http dns',

  // Object Oriented Programming
  'oops': 'object oriented programming classes inheritance polymorphism encapsulation abstraction interface method overloading overriding constructor',
  'oop': 'object oriented programming classes inheritance polymorphism encapsulation abstraction interface method overloading overriding constructor',
  'object oriented': 'oop oops classes inheritance polymorphism encapsulation abstraction',

  // Machine Learning & AI
  'ml': 'machine learning supervised unsupervised regression classification clustering neural network deep learning training model prediction feature',
  'machine learning': 'ml supervised unsupervised regression classification clustering neural network deep learning training',
  'ai': 'artificial intelligence machine learning deep learning neural network natural language processing computer vision nlp reinforcement learning',
  'artificial intelligence': 'ai machine learning deep learning neural network nlp computer vision',
  'dl': 'deep learning neural network convolutional recurrent transformer attention backpropagation gradient descent',
  'deep learning': 'dl neural network cnn rnn transformer attention mechanism backpropagation',

  // Compiler Design
  'cd': 'compiler design lexical analysis parsing syntax semantic code generation optimization grammar automata regular expression',
  'compiler': 'compiler design lexical analysis parsing syntax directed translation code generation optimization',
  'compiler design': 'cd lexical analysis parsing syntax semantic code generation optimization grammar',

  // Software Engineering
  'se': 'software engineering sdlc agile waterfall testing requirements design patterns uml use case',
  'software engineering': 'se sdlc agile waterfall testing requirements design patterns uml',

  // Discrete Mathematics
  'dm': 'discrete mathematics logic propositional predicate sets relations functions graph theory combinatorics probability',
  'discrete math': 'dm logic propositional predicate sets relations functions graph theory combinatorics',
  'discrete mathematics': 'dm logic propositional predicate sets relations functions graph theory combinatorics',

  // Digital Logic / Electronics
  'dld': 'digital logic design boolean algebra gates flip flop counter register combinational sequential circuit multiplexer decoder',
  'digital logic': 'dld boolean algebra gates flip flop counter register combinational sequential circuit',

  // Computer Architecture
  'coa': 'computer organization architecture cpu pipeline cache memory instruction set addressing mode register alu',
  'computer architecture': 'coa cpu pipeline cache memory instruction set addressing mode register',

  // Web Development
  'web dev': 'web development html css javascript react nodejs frontend backend api rest http server client',
  'web development': 'html css javascript react nodejs angular vue frontend backend api rest http',
  'frontend': 'html css javascript react angular vue dom component ui ux responsive layout',
  'backend': 'server api rest nodejs express django flask database sql mongodb authentication routing middleware',

  // Mathematics
  'math': 'mathematics calculus algebra trigonometry geometry statistics probability linear algebra differential integral',
  'maths': 'mathematics calculus algebra trigonometry geometry statistics probability linear algebra differential integral',
  'calculus': 'mathematics differential integral limits derivatives continuity functions series sequences',
  'linear algebra': 'matrices vectors eigenvalues determinants spaces transformations rank',

  // Physics
  'physics': 'mechanics thermodynamics electromagnetism optics quantum waves motion force energy momentum',

  // Chemistry
  'chemistry': 'organic inorganic physical chemical reactions bonds molecules atoms periodic table equilibrium',
};

/**
 * Expand a goal text using the abbreviation map.
 * Returns { originalWords: string[], expandedWords: string[] }
 * expandedWords are the ADDITIONAL terms not in the original.
 */
function expandGoalText(goalText) {
  const normalized = goalText.toLowerCase().trim();
  const originalWords = normalized
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1); // Allow 2-char words for abbreviations like "os", "ml", "ai"

  const expandedWords = [];

  // Check the full goal text first (e.g., "theory of computation")
  if (GOAL_EXPANSIONS[normalized]) {
    const terms = GOAL_EXPANSIONS[normalized].split(/\s+/).filter(w => w.length > 1);
    expandedWords.push(...terms);
  }

  // Check each individual word (e.g., "toc" from "toc study")
  for (const word of originalWords) {
    if (GOAL_EXPANSIONS[word]) {
      const terms = GOAL_EXPANSIONS[word].split(/\s+/).filter(w => w.length > 1);
      expandedWords.push(...terms);
    }
  }

  // Check multi-word combinations (e.g., "data structures" from "data structures and algorithms")
  const fullText = originalWords.join(' ');
  for (const key of Object.keys(GOAL_EXPANSIONS)) {
    if (key.includes(' ') && fullText.includes(key)) {
      const terms = GOAL_EXPANSIONS[key].split(/\s+/).filter(w => w.length > 1);
      expandedWords.push(...terms);
    }
  }

  // Deduplicate expanded words and remove any that are already in original
  const origSet = new Set(originalWords);
  const uniqueExpanded = [...new Set(expandedWords)].filter(w => !origSet.has(w));

  return { originalWords, expandedWords: uniqueExpanded };
}

/**
 * Compute goal relevance using fuzzy matching + abbreviation expansion.
 * More aggressive than computeGoalSimilarity — uses substring, prefix,
 * cross-word matching, AND synonym expansion to catch abbreviations.
 * 
 * Used by the goal-relevance adjustment stage in the classifier.
 *
 * @param {Object} extractedContent — { title, url, hostname, content }
 * @param {string} goalText — Session goal text
 * @returns {{ score: number, expandedMatchCount: number, hasExpansion: boolean }}
 */
export function computeGoalRelevance(extractedContent, goalText) {
  if (!goalText) return { score: 0, expandedMatchCount: 0, hasExpansion: false };

  const title = (extractedContent.title || '').toLowerCase();
  const content = (extractedContent.content || '').toLowerCase();
  const url = (extractedContent.url || '').toLowerCase();
  // Title gets double weight — it's the strongest topical indicator
  const allText = [title, title, content, url].join(' ');

  // ── Expand goal text using abbreviation map ──
  const { originalWords, expandedWords } = expandGoalText(goalText);

  // Filter original words: only use words > 2 chars for matching (but expansion already happened)
  const goalWordsForMatch = originalWords.filter(w => w.length > 2);

  if (goalWordsForMatch.length === 0 && expandedWords.length === 0) return 0;

  const contentTokens = allText
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2);
  const contentWordSet = new Set(contentTokens);

  let totalScore = 0;
  let totalWeight = 0;

  // ── Score original goal words (weight: 1.0 each) ──
  for (const goalWord of goalWordsForMatch) {
    totalWeight += 1.0;

    // 1. Exact match (strongest signal)
    if (contentWordSet.has(goalWord)) {
      totalScore += 1.0;
      continue;
    }

    // 2. Substring + prefix fuzzy matching
    let bestPartial = 0;
    for (const cw of contentWordSet) {
      // Goal word found inside a content word (e.g., "data" in "database")
      if (cw.length > goalWord.length && cw.includes(goalWord) && goalWord.length >= 3) {
        bestPartial = Math.max(bestPartial, 0.8);
      }
      // Content word found inside goal word (e.g., "base" in "database")
      if (goalWord.length > cw.length && goalWord.includes(cw) && cw.length >= 4) {
        bestPartial = Math.max(bestPartial, 0.6);
      }
      // Shared prefix (e.g., "program" ↔ "programming")
      if (goalWord.length >= 4 && cw.length >= 4) {
        const prefixLen = Math.min(5, Math.min(goalWord.length, cw.length));
        if (goalWord.substring(0, prefixLen) === cw.substring(0, prefixLen)) {
          bestPartial = Math.max(bestPartial, 0.5);
        }
      }
    }
    totalScore += bestPartial;
  }

  // ── Score expanded words (weight: 0.7 each — slightly lower to avoid over-boosting) ──
  // Only count up to the top N matches to avoid one big expansion dominating
  const EXPANDED_WEIGHT = 0.7;
  const MAX_EXPANDED_MATCHES = 8; // Cap how many expanded terms contribute
  let expandedMatches = 0;

  for (const ew of expandedWords) {
    if (ew.length < 3) continue; // Skip very short expanded terms
    if (expandedMatches >= MAX_EXPANDED_MATCHES) break;

    let matchScore = 0;

    // Exact match
    if (contentWordSet.has(ew)) {
      matchScore = 1.0;
    } else {
      // Fuzzy: content word contains expanded word or vice versa
      for (const cw of contentWordSet) {
        if (cw.length > ew.length && cw.includes(ew) && ew.length >= 3) {
          matchScore = Math.max(matchScore, 0.7);
        }
        if (ew.length > cw.length && ew.includes(cw) && cw.length >= 4) {
          matchScore = Math.max(matchScore, 0.5);
        }
        if (ew.length >= 4 && cw.length >= 4) {
          const prefixLen = Math.min(5, Math.min(ew.length, cw.length));
          if (ew.substring(0, prefixLen) === cw.substring(0, prefixLen)) {
            matchScore = Math.max(matchScore, 0.4);
          }
        }
      }
    }

    if (matchScore > 0) {
      totalScore += matchScore * EXPANDED_WEIGHT;
      totalWeight += EXPANDED_WEIGHT;
      expandedMatches++;
    }
  }

  // If we only have expanded words (e.g., goal is "toc" which is ≤2 chars after filtering),
  // use expanded weight as the denominator
  if (totalWeight === 0) return { score: 0, expandedMatchCount: 0, hasExpansion: expandedWords.length > 0 };

  return {
    score: totalScore / totalWeight,
    expandedMatchCount: expandedMatches,
    hasExpansion: expandedWords.length > 0,
  };
}

/**
 * Extract a full feature vector from extracted content + session context.
 *
 * @param {Object} extractedContent — { title, url, hostname, content }
 * @param {string} sessionGoal — Current session goal text
 * @returns {{ vector: Float64Array, contentType: string }}
 */
export function extractFeatures(extractedContent, sessionGoal = '') {
  if (!_vocabulary) initFeatures();

  const title = extractedContent.title || '';
  const url = extractedContent.url || '';
  const hostname = extractedContent.hostname || '';
  const content = extractedContent.content || '';

  // Combine all text, give title 3x weight
  const allText = [title, title, title, url, hostname, content].join(' ');
  const vec = buildTFVector(allText);

  // ─── Meta features (appended after vocabulary features) ───
  const metaStart = _vocabulary.length;

  // 1. Goal similarity (0-1)
  const goalSim = computeGoalSimilarity(sessionGoal, allText);
  vec[metaStart + 0] = goalSim;

  // 2. URL depth (number of path segments, normalized)
  try {
    const urlObj = new URL(url.startsWith('http') ? url : 'https://' + url);
    vec[metaStart + 1] = Math.min(urlObj.pathname.split('/').filter(Boolean).length / 5, 1);
  } catch { vec[metaStart + 1] = 0; }

  // 3. Content length bucket (0-1)
  vec[metaStart + 2] = Math.min(content.length / 5000, 1);

  // 4. Has video content (0 or 1)
  const ct = detectContentType(extractedContent);
  vec[metaStart + 3] = ct === 'video' ? 1 : 0;

  // 5. Has code/interactive content (0 or 1)
  vec[metaStart + 4] = ct === 'interactive' ? 1 : 0;

  // 6. Has audio content (0 or 1)
  vec[metaStart + 5] = ct === 'audio' ? 1 : 0;

  // 7. Is YouTube (0 or 1)
  vec[metaStart + 6] = hostname.includes('youtube.com') ? 1 : 0;

  // 8. TLD education/org signal (0 or 1)
  const eduTLDs = ['.edu', '.ac.', '.org', '.gov'];
  vec[metaStart + 7] = eduTLDs.some(tld => hostname.includes(tld)) ? 1 : 0;

  // 9. Podcast content detected (0 or 1) — works across any site
  const podcastSignals = ['podcast', 'episode', 'hosted by', 'listen now', 'show notes', 'subscribe to podcast'];
  const isPodcast = podcastSignals.some(sig => allText.includes(sig)) ? 1 : 0;
  vec[metaStart + 8] = isPodcast;

  // 10. Has structured data (0 or 1) — content-rich pages tend to have schema.org data
  const hasStructured = (extractedContent.structuredDataFound) ? 1 : 0;
  vec[metaStart + 9] = hasStructured;

  return { vector: vec, contentType: ct };
}

/**
 * Extract features from a training data entry (for building the model).
 */
export function extractTrainingFeatures(entry) {
  return extractFeatures({
    title: entry.title,
    url: entry.url,
    hostname: entry.url.split('/')[0] || '',
    content: entry.snippet,
  }, '');
}

/**
 * Get the vocabulary size (for Naive Bayes initialization).
 */
export function getVocabSize() {
  if (!_vocabulary) initFeatures();
  return _vocabulary.length + META_FEATURES_COUNT;
}
