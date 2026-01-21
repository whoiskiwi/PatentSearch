"""
Thinkstruct Patent Hybrid Search Engine

Supports three search scenarios:
1. Invalidity Search - Find prior art earlier than the target patent
2. Infringement Monitoring - Monitor new patents for potential infringement
3. Patentability Review - Evaluate patentability of new inventions

Uses PatentSBERTa_V2 patent-specific model for semantic search
https://huggingface.co/AAUBS/PatentSBERTa_V2
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes - By Scenario
# ============================================================================

@dataclass
class InvalidityResult:
    """
    Invalidity search result.

    Used to find prior art that may invalidate a target patent.
    Contains similarity score, matched claims, and independent claims.
    """
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    matched_claims: list[str] = field(default_factory=list)
    independent_claims: list[str] = field(default_factory=list)
    claims_count: int = 0
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class InfringementResult:
    """
    Infringement monitoring result.

    Used to detect patents that may infringe on user's patent rights.
    Contains risk level assessment and overlapping technical features.
    """
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    risk_level: str = ""
    matched_claims: list[str] = field(default_factory=list)
    overlapping_features: list[str] = field(default_factory=list)
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class PatentabilityResult:
    """
    Patentability review result.

    Used to evaluate the patentability of a new invention.
    Contains novelty assessment and key differences from prior art.
    """
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    novelty_assessment: str = ""
    closest_prior_art: bool = False
    key_differences: list[str] = field(default_factory=list)
    matched_claims: list[str] = field(default_factory=list)
    technical_field: str = ""
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


@dataclass
class PatentIdSearchResult:
    """
    Patent ID search result.

    Used when searching by patent document number instead of text query.
    """
    doc_number: str
    title: str
    abstract: str
    classification: str
    publication_date: str
    similarity_score: float
    matched_claims: list[str] = field(default_factory=list)
    all_claims: list[str] = field(default_factory=list)
    detailed_description: str = ""


# ============================================================================
# Search Engine Core Class
# ============================================================================

class PatentSearchEngine:
    """
    Patent Hybrid Search Engine.

    Combines semantic search (PatentSBERTa) with traditional filtering
    to provide accurate patent similarity search across multiple scenarios.

    Attributes:
        data_path: Path to the patent JSON data file
        embeddings_path: Path to pre-computed embeddings (.npy file)
        patents: List of patent records loaded from JSON
        embeddings: Pre-computed patent vectors (numpy array)
        model: PatentSBERTa sentence transformer model
    """

    # IPC Classification code to technical field mapping
    CLASSIFICATION_FIELDS = {
        'A': 'Human Necessities',
        'B': 'Performing Operations; Transporting',
        'C': 'Chemistry; Metallurgy',
        'D': 'Textiles; Paper',
        'E': 'Fixed Constructions',
        'F': 'Mechanical Engineering',
        'G': 'Physics',
        'H': 'Electricity',
    }

    def __init__(self, data_path: str | Path):
        """
        Initialize the search engine.

        Args:
            data_path: Path to the cleaned patent JSON data file
        """
        self.data_path = Path(data_path)
        self.embeddings_path = self.data_path.with_suffix('.embeddings.npy')
        self.patents: list[dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.model = None
        self._load_data()
        self._load_or_build_embeddings()

    # ========================================================================
    # Data Loading Methods
    # ========================================================================

    def _load_data(self) -> None:
        """
        Load patent data from JSON file.

        Also builds an index mapping doc_number to array index for fast lookup.
        """
        logger.info(f"Loading patent data: {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.patents = json.load(f)
        logger.info(f"Load complete: {len(self.patents)} patent records")
        # Build doc_number index for fast lookup
        self._doc_index = {p["doc_number"]: i for i, p in enumerate(self.patents)}

    def get_patent_by_id(self, doc_number: str) -> Optional[dict]:
        """
        Get a patent record by its document number.

        Supports flexible matching - handles variations like "US12345678",
        "12345678", "US-12345678" etc.

        Args:
            doc_number: Patent document number (with or without prefix)

        Returns:
            Patent record dict if found, None otherwise
        """
        # Normalize doc_number (remove prefix like US, spaces, etc.)
        normalized = doc_number.strip().upper().replace("US", "").replace("-", "").replace(" ", "")

        # Try exact match first
        if doc_number in self._doc_index:
            return self.patents[self._doc_index[doc_number]]

        # Try normalized match
        for patent in self.patents:
            patent_num = patent["doc_number"].upper().replace("US", "").replace("-", "").replace(" ", "")
            if patent_num == normalized or patent["doc_number"] == doc_number:
                return patent

        return None

    # ========================================================================
    # Model & Embeddings Methods
    # ========================================================================

    def _load_model(self) -> None:
        """
        Lazy load the PatentSBERTa semantic search model.

        Model is only loaded when first needed to reduce startup time.
        The model (~420MB) is cached locally after first download.
        """
        if self.model is None:
            logger.info("Loading semantic search model PatentSBERTa_V2...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('AAUBS/PatentSBERTa_V2')
            logger.info("Model loaded successfully")

    def _load_or_build_embeddings(self) -> None:
        """
        Load pre-computed embeddings from file, or build and save them.

        This optimization dramatically speeds up search:
        - First run: Compute embeddings for all patents (~50 sec), save to .npy file
        - Subsequent runs: Load from file (~0.5 sec)
        """
        if self.embeddings_path.exists():
            logger.info(f"Loading pre-computed embeddings from {self.embeddings_path}")
            self.embeddings = np.load(self.embeddings_path)
            logger.info(f"Embeddings loaded: {self.embeddings.shape}")
        else:
            logger.info("No pre-computed embeddings found, building now...")
            self._build_embeddings()

    def _build_embeddings(self) -> None:
        """
        Build vector representations for all patents and save to file.

        Each patent is converted to a 768-dimensional vector using:
        - Title
        - Abstract
        - First 3 claims

        The embeddings are saved to a .npy file for fast loading on restart.
        """
        if self.embeddings is not None:
            return

        self._load_model()
        logger.info("Building patent vector index...")

        # Combine title, abstract, and top claims for each patent
        texts = []
        for patent in self.patents:
            claims_text = " ".join(patent.get("claims", [])[:3])
            combined = f"{patent['title']} {patent['abstract']} {claims_text}"
            texts.append(combined)

        # Encode all patents using the model
        self.embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Save embeddings to file for future use
        np.save(self.embeddings_path, self.embeddings)
        logger.info(f"Embeddings built and saved to {self.embeddings_path}: {self.embeddings.shape}")

    def _compute_similarity(self, query: str, top_k: int = 100) -> list[tuple[int, float]]:
        """
        Compute semantic similarity between query and all patents.

        Uses cosine similarity: similarity = (A · B) / (|A| × |B|)

        Args:
            query: Search query text
            top_k: Number of top results to return

        Returns:
            List of (patent_index, similarity_score) tuples, sorted by score descending
        """
        self._load_model()  # Ensure model is loaded for query encoding

        # Encode the query text to a vector
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]

        # Compute cosine similarity with all patent embeddings
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get top K indices sorted by similarity
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    # ========================================================================
    # Feature Extraction Methods
    # ========================================================================

    def _extract_independent_claims(self, claims: list[str]) -> list[str]:
        """
        Extract independent claims from a list of claims.

        Independent claims don't reference other claims (no "claim 1" or "claims 1-3").
        The first claim is always considered independent.

        Args:
            claims: List of claim texts

        Returns:
            List of independent claims (max 3)
        """
        independent = []
        for i, claim in enumerate(claims):
            # Check if claim references other claims
            if not re.search(r'claim\s+\d+|claims\s+\d+', claim.lower()):
                independent.append(claim)
            elif i == 0:
                # First claim is always independent
                independent.append(claim)
        return independent[:3]

    def _find_matched_claims(self, query: str, claims: list[str], threshold: float = 0.5) -> list[str]:
        """
        Find claims that semantically match the query.

        Uses cosine similarity to find claims above the threshold.

        Args:
            query: Search query text
            claims: List of claim texts to search
            threshold: Minimum similarity score (0-1) to consider a match

        Returns:
            List of matching claims (max 5)
        """
        if not claims or self.model is None:
            return []

        self._load_model()

        # Encode query and all claims
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        claims_embeddings = self.model.encode(claims, convert_to_numpy=True)

        # Find claims above threshold
        matched = []
        for i, claim_emb in enumerate(claims_embeddings):
            sim = np.dot(query_embedding, claim_emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(claim_emb)
            )
            if sim >= threshold:
                matched.append(claims[i])

        return matched[:5]

    def _extract_technical_features(self, text: str) -> list[str]:
        """
        Extract technical features from patent text.

        Looks for common patent claim patterns like:
        - "comprising X"
        - "including X"
        - "having X"
        - "configured to X"
        - "adapted to X"

        Args:
            text: Patent text (claims, abstract, etc.)

        Returns:
            List of extracted feature phrases (max 10)
        """
        features = []
        patterns = [
            r'comprising\s+([^,;.]+)',
            r'including\s+([^,;.]+)',
            r'having\s+([^,;.]+)',
            r'configured to\s+([^,;.]+)',
            r'adapted to\s+([^,;.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                feature = match.strip()
                # Filter by reasonable length
                if 10 < len(feature) < 100:
                    features.append(feature)

        return list(set(features))[:10]

    def _find_overlapping_features(self, query_features: list[str], patent: dict) -> list[str]:
        """
        Find technical features that overlap between query and patent.

        A feature is considered overlapping if at least 50% of its
        keywords (words > 3 chars) appear in the patent text.

        Args:
            query_features: List of features extracted from query
            patent: Patent record to compare against

        Returns:
            List of overlapping feature phrases
        """
        patent_text = f"{patent['title']} {patent['abstract']} {' '.join(patent.get('claims', []))}"
        patent_text_lower = patent_text.lower()

        overlapping = []
        for feature in query_features:
            # Extract significant keywords (> 3 characters)
            keywords = [w for w in feature.split() if len(w) > 3]
            if keywords:
                # Check if at least 50% of keywords match
                match_count = sum(1 for kw in keywords if kw in patent_text_lower)
                if match_count >= len(keywords) * 0.5:
                    overlapping.append(feature)

        return overlapping

    def _identify_key_differences(self, query: str, patent: dict) -> list[str]:
        """
        Identify key differences between query and prior art patent.

        Extracts features from both texts and finds features unique to the query.

        Args:
            query: User's invention description or claims
            patent: Prior art patent to compare against

        Returns:
            List of novel features not found in prior art (max 5)
        """
        query_features = set(self._extract_technical_features(query))
        patent_features = set(self._extract_technical_features(
            f"{patent['abstract']} {' '.join(patent.get('claims', [])[:3])}"
        ))

        unique_features = query_features - patent_features
        return [f"Novel feature: {f}" for f in list(unique_features)[:5]]

    # ========================================================================
    # Assessment Methods
    # ========================================================================

    def _calculate_risk_level(self, similarity: float) -> str:
        """
        Calculate infringement risk level based on similarity score.

        Risk levels:
        - Very High: > 0.9 (nearly identical)
        - High: >= 0.7 (significant overlap)
        - Medium: >= 0.5 (some similarity)
        - Low: < 0.5 (minimal risk)

        Args:
            similarity: Cosine similarity score (0-1)

        Returns:
            Risk level string
        """
        if similarity > 0.9:
            return "Very High"
        elif similarity >= 0.7:
            return "High"
        elif similarity >= 0.5:
            return "Medium"
        return "Low"

    def _assess_novelty(self, similarity: float) -> str:
        """
        Assess novelty of invention based on similarity to prior art.

        Assessments:
        - Identical: > 0.85 (invention likely not novel)
        - Similar: >= 0.6 (significant prior art exists)
        - Novel: < 0.6 (potentially patentable)

        Args:
            similarity: Cosine similarity score (0-1)

        Returns:
            Novelty assessment string
        """
        if similarity > 0.85:
            return "Identical"
        elif similarity >= 0.6:
            return "Similar"
        return "Novel"

    def _get_technical_field(self, classification: str) -> str:
        """
        Get technical field name from IPC/CPC classification code.

        Uses the first character of the classification code.

        Args:
            classification: IPC/CPC classification code (e.g., "B60C")

        Returns:
            Technical field name (e.g., "Performing Operations; Transporting")
        """
        if classification:
            first_char = classification[0].upper()
            return self.CLASSIFICATION_FIELDS.get(first_char, "Unknown")
        return "Unknown"

    # ========================================================================
    # Filter Methods
    # ========================================================================

    def _filter_by_classification(self, candidates: list[tuple[int, float]], prefix: str) -> list[tuple[int, float]]:
        """
        Filter candidates by classification code prefix.

        Args:
            candidates: List of (index, score) tuples
            prefix: Classification prefix to match (e.g., "B60" matches "B60C", "B60B")

        Returns:
            Filtered list of candidates
        """
        if not prefix:
            return candidates
        prefix_upper = prefix.upper()
        return [
            (idx, score) for idx, score in candidates
            if self.patents[idx].get("classification", "").upper().startswith(prefix_upper)
        ]

    def _filter_by_date(self, candidates: list[tuple[int, float]],
                        date_from: Optional[str], date_to: Optional[str]) -> list[tuple[int, float]]:
        """
        Filter candidates by publication date range.

        Args:
            candidates: List of (index, score) tuples
            date_from: Start date (YYYY-MM-DD), inclusive
            date_to: End date (YYYY-MM-DD), inclusive

        Returns:
            Filtered list of candidates within date range
        """
        if not date_from and not date_to:
            return candidates

        filtered = []
        for idx, score in candidates:
            pub_date = self.patents[idx].get("publication_date", "")
            if not pub_date:
                continue
            if date_from and pub_date < date_from:
                continue
            if date_to and pub_date > date_to:
                continue
            filtered.append((idx, score))

        return filtered

    def _filter_by_keywords(self, candidates: list[tuple[int, float]], keywords: list[str]) -> list[tuple[int, float]]:
        """
        Filter candidates by required keywords.

        All keywords must be present in the patent's title, abstract, or claims.
        Uses AND logic - patent must contain all keywords.

        Args:
            candidates: List of (index, score) tuples
            keywords: List of required keywords

        Returns:
            Filtered list of candidates containing all keywords
        """
        if not keywords:
            return candidates

        filtered = []
        for idx, score in candidates:
            patent = self.patents[idx]
            # Combine searchable text fields
            searchable_text = (
                patent.get("title", "") + " " +
                patent.get("abstract", "") + " " +
                " ".join(patent.get("claims", []))
            ).lower()

            # Check if all keywords are present (AND logic)
            if all(kw.lower() in searchable_text for kw in keywords):
                filtered.append((idx, score))

        return filtered

    def _filter_by_title(self, candidates: list[tuple[int, float]], title_query: str) -> list[tuple[int, float]]:
        """
        Filter candidates by title substring match.

        Case-insensitive partial match on patent title.

        Args:
            candidates: List of (index, score) tuples
            title_query: Substring to search for in titles

        Returns:
            Filtered list of candidates with matching titles
        """
        if not title_query:
            return candidates

        title_query_lower = title_query.lower().strip()
        return [
            (idx, score) for idx, score in candidates
            if title_query_lower in self.patents[idx].get("title", "").lower()
        ]

    # ========================================================================
    # Scenario-based Search APIs
    # ========================================================================

    def invalidity_search(
        self,
        query_claims: str,
        query_doc_number: str = "",
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        target_date: Optional[str] = None,
        top_k: int = 20
    ) -> list[InvalidityResult]:
        """
        Invalidity search: Find prior art that may invalidate a target patent.

        Searches for patents published BEFORE the target date that are
        semantically similar to the query claims.

        Args:
            query_claims: Claims text to search for prior art
            query_doc_number: Optional document number for reference
            classification: Filter by IPC/CPC classification prefix
            keywords: Filter by required keywords
            title_search: Filter by title substring
            target_date: Only return patents published before this date
            top_k: Maximum number of results to return

        Returns:
            List of InvalidityResult objects sorted by similarity
        """
        logger.info(f"Executing invalidity search: query_length={len(query_claims)}")

        # Compute similarity and apply filters
        candidates = self._compute_similarity(query_claims, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)

        # For invalidity, only consider patents before target date
        if target_date:
            candidates = self._filter_by_date(candidates, None, target_date)

        # Build result objects
        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = InvalidityResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                matched_claims=self._find_matched_claims(query_claims, claims),
                independent_claims=self._extract_independent_claims(claims),
                claims_count=len(claims),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Invalidity search complete: {len(results)} results returned")
        return results

    def infringement_search(
        self,
        my_claims: str,
        my_doc_number: str,
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_similarity: float = 0.5,
        top_k: int = 20
    ) -> list[InfringementResult]:
        """
        Infringement monitoring: Find patents that may infringe on your rights.

        Searches for patents that are semantically similar to your claims
        and assesses the infringement risk level.

        Args:
            my_claims: Your patent claims to monitor
            my_doc_number: Your patent document number (excluded from results)
            classification: Filter by IPC/CPC classification prefix
            keywords: Filter by required keywords
            title_search: Filter by title substring
            date_from: Only return patents published after this date
            date_to: Only return patents published before this date
            min_similarity: Minimum similarity threshold (0-1)
            top_k: Maximum number of results to return

        Returns:
            List of InfringementResult objects with risk assessments
        """
        logger.info(f"Executing infringement monitoring: my_doc_number={my_doc_number}")

        # Extract features from user's claims for overlap analysis
        my_features = self._extract_technical_features(my_claims)

        # Compute similarity and apply filters
        candidates = self._compute_similarity(my_claims, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_date(candidates, date_from, date_to)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)

        # Filter by minimum similarity
        candidates = [(idx, score) for idx, score in candidates if score >= min_similarity]

        # Build result objects
        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]

            # Skip user's own patent
            if patent["doc_number"] == my_doc_number:
                continue

            claims = patent.get("claims", [])
            overlapping = self._find_overlapping_features(my_features, patent)

            result = InfringementResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                risk_level=self._calculate_risk_level(score),
                matched_claims=self._find_matched_claims(my_claims, claims),
                overlapping_features=overlapping,
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Infringement monitoring complete: {len(results)} results returned")
        return results

    def patentability_search(
        self,
        invention_description: str,
        draft_claims: str = "",
        classification: str = "",
        keywords: list[str] = None,
        title_search: str = "",
        top_k: int = 20
    ) -> list[PatentabilityResult]:
        """
        Patentability review: Evaluate if an invention is patentable.

        Searches for prior art similar to the invention and assesses novelty.
        Lower similarity scores indicate better patentability.

        Args:
            invention_description: Description of the new invention
            draft_claims: Optional draft claims for more precise search
            classification: Filter by IPC/CPC classification prefix
            keywords: Filter by required keywords
            title_search: Filter by title substring
            top_k: Maximum number of results to return

        Returns:
            List of PatentabilityResult objects with novelty assessments
        """
        logger.info(f"Executing patentability review: desc_length={len(invention_description)}")

        # Combine description and draft claims for search
        query = invention_description
        if draft_claims:
            query = f"{invention_description} {draft_claims}"

        # Compute similarity and apply filters
        candidates = self._compute_similarity(query, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)
        candidates = self._filter_by_keywords(candidates, keywords or [])
        candidates = self._filter_by_title(candidates, title_search)

        # Build result objects
        results = []
        for i, (idx, score) in enumerate(candidates[:top_k]):
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = PatentabilityResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                novelty_assessment=self._assess_novelty(score),
                closest_prior_art=(i == 0),  # First result is closest
                key_differences=self._identify_key_differences(query, patent),
                matched_claims=self._find_matched_claims(query, claims),
                technical_field=self._get_technical_field(patent["classification"]),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Patentability review complete: {len(results)} results returned")
        return results

    def search_by_patent_id(
        self,
        doc_number: str,
        classification: str = "",
        top_k: int = 20
    ) -> tuple[Optional[dict], list[PatentIdSearchResult]]:
        """
        Search for similar patents using a patent ID as input.

        Looks up the source patent by document number and finds similar patents
        based on its abstract and claims.

        Args:
            doc_number: Patent document number to use as query
            classification: Filter by IPC/CPC classification prefix
            top_k: Maximum number of results to return

        Returns:
            Tuple of (source_patent, similar_patents):
            - source_patent: The patent record matching doc_number, or None
            - similar_patents: List of similar PatentIdSearchResult objects
        """
        logger.info(f"Executing patent ID search: doc_number={doc_number}")

        # Find the source patent
        source_patent = self.get_patent_by_id(doc_number)
        if source_patent is None:
            logger.warning(f"Patent not found: {doc_number}")
            return None, []

        # Build query from source patent's claims and abstract
        claims_text = " ".join(source_patent.get("claims", [])[:5])
        query = f"{source_patent['abstract']} {claims_text}"

        # Search for similar patents
        candidates = self._compute_similarity(query, top_k=100)
        candidates = self._filter_by_classification(candidates, classification)

        # Exclude the source patent itself
        source_idx = self._doc_index.get(source_patent["doc_number"])
        candidates = [(idx, score) for idx, score in candidates if idx != source_idx]

        # Build result objects
        results = []
        for idx, score in candidates[:top_k]:
            patent = self.patents[idx]
            claims = patent.get("claims", [])

            result = PatentIdSearchResult(
                doc_number=patent["doc_number"],
                title=patent["title"],
                abstract=patent["abstract"],
                classification=patent["classification"],
                publication_date=patent["publication_date"],
                similarity_score=round(score, 4),
                matched_claims=self._find_matched_claims(query, claims),
                all_claims=claims[:10],
                detailed_description=patent.get("detailed_description", "")[:500]
            )
            results.append(result)

        logger.info(f"Patent ID search complete: {len(results)} results returned")
        return source_patent, results


# ============================================================================
# Utility Functions
# ============================================================================

def get_latest_data_file(output_dir: str | Path) -> Path:
    """
    Get the latest cleaned patent data file from a directory.

    Looks for files matching pattern "patents_cleaned_*.json" and
    returns the most recent one (by filename sort order).

    Args:
        output_dir: Directory containing cleaned patent data files

    Returns:
        Path to the latest cleaned data file

    Raises:
        FileNotFoundError: If no matching files found
    """
    output_path = Path(output_dir)
    files = sorted(output_path.glob("patents_cleaned_*.json"))
    if not files:
        raise FileNotFoundError(f"Cleaned data file not found: {output_path}")
    return files[-1]
