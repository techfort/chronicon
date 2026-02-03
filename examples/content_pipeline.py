"""
Example: Content Pipeline Workflow

This example demonstrates:
- Sequential processing pipeline
- Validation and error handling
- Conditional logic based on LLM outputs
- Structured data transformations

Use case: Process a blog post draft through multiple stages:
1. Analyze tone and style
2. Suggest improvements
3. Rewrite sections if needed
4. Generate SEO metadata
"""

from chronicon import workflow, execute, replay, llm_call
from chronicon.log import ExecutionLog
from typing import Dict, List, Optional
import json


@workflow
def content_pipeline(
    draft: str,
    target_tone: str = "professional",
    auto_improve: bool = True
) -> Dict:
    """
    Process a content draft through analysis and improvement pipeline.
    
    Args:
        draft: The original draft text
        target_tone: Desired tone (professional, casual, technical, etc.)
        auto_improve: Whether to automatically apply improvements
        
    Returns:
        Dictionary with analysis, suggestions, final version, and metadata
    """
    print(f"\n📄 Processing content draft ({len(draft)} characters)")
    print(f"   Target tone: {target_tone}")
    print(f"   Auto-improve: {auto_improve}")
    print("=" * 70)
    
    # Stage 1: Analyze current content
    print("\n🔍 Stage 1: Analyzing content...")
    analysis_raw = llm_call(
        prompt=f"""Analyze this content draft. Provide a JSON response with:
- tone: current tone (professional/casual/technical/etc)
- clarity_score: 1-10
- engagement_score: 1-10
- issues: list of specific issues found
- strengths: list of strengths

Draft:
{draft}

JSON response:""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.3,
        max_tokens=500,
    )
    
    # Parse analysis
    try:
        analysis = json.loads(analysis_raw.strip())
    except json.JSONDecodeError:
        analysis = {
            "tone": "unknown",
            "clarity_score": 5,
            "engagement_score": 5,
            "issues": ["Could not parse analysis"],
            "strengths": [],
        }
    
    print(f"   Current tone: {analysis.get('tone', 'unknown')}")
    print(f"   Clarity: {analysis.get('clarity_score', 0)}/10")
    print(f"   Engagement: {analysis.get('engagement_score', 0)}/10")
    
    # Stage 2: Generate improvement suggestions
    print("\n💡 Stage 2: Generating improvement suggestions...")
    suggestions = llm_call(
        prompt=f"""Based on this analysis, suggest 3-5 specific improvements to make the content more {target_tone}:

Current analysis:
- Tone: {analysis.get('tone')}
- Clarity: {analysis.get('clarity_score')}/10
- Issues: {', '.join(analysis.get('issues', []))}

Original draft:
{draft}

Provide numbered suggestions (1., 2., etc.):""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.5,
        max_tokens=400,
    )
    
    suggestion_list = [s.strip() for s in suggestions.split('\n') if s.strip() and s[0].isdigit()]
    print(f"   Generated {len(suggestion_list)} suggestions")
    
    # Stage 3: Apply improvements (if auto_improve)
    improved_draft = draft
    if auto_improve and analysis.get('clarity_score', 10) < 8:
        print("\n✨ Stage 3: Applying improvements...")
        improved_draft = llm_call(
            prompt=f"""Improve this draft by applying these suggestions:

Suggestions:
{suggestions}

Target tone: {target_tone}

Original draft:
{draft}

Improved version:""",
            model="claude-3-5-sonnet-20241022",
            temperature=0.4,
            max_tokens=1000,
        )
        print(f"   Applied improvements ({len(improved_draft)} characters)")
    else:
        print("\n⏭️  Stage 3: Skipping improvements (not needed or disabled)")
    
    # Stage 4: Generate SEO metadata
    print("\n🔎 Stage 4: Generating SEO metadata...")
    seo_raw = llm_call(
        prompt=f"""Generate SEO metadata for this content. Return JSON with:
- title: SEO-optimized title (50-60 chars)
- description: meta description (150-160 chars)
- keywords: array of 5-7 keywords

Content:
{improved_draft}

JSON response:""",
        model="claude-3-5-sonnet-20241022",
        temperature=0.4,
        max_tokens=300,
    )
    
    # Parse SEO metadata
    try:
        seo = json.loads(seo_raw.strip())
    except json.JSONDecodeError:
        seo = {
            "title": "Untitled",
            "description": "",
            "keywords": [],
        }
    
    print(f"   Title: {seo.get('title', 'N/A')}")
    print(f"   Keywords: {len(seo.get('keywords', []))}")
    
    # Calculate improvement metrics
    was_improved = auto_improve and improved_draft != draft
    improvement_pct = 0
    if was_improved:
        improvement_pct = int(((len(improved_draft) - len(draft)) / len(draft)) * 100)
    
    return {
        "original_draft": draft,
        "final_draft": improved_draft,
        "was_improved": was_improved,
        "improvement_percent": improvement_pct,
        "analysis": analysis,
        "suggestions": suggestion_list,
        "seo": seo,
        "target_tone": target_tone,
        "pipeline_stages": 4,
    }


def main():
    """Run the content pipeline example."""
    print("\n" + "=" * 70)
    print("CHRONICON EXAMPLE: Content Pipeline")
    print("=" * 70)
    
    # Sample draft
    draft = """
    We built a new feature. It's really cool and we think users will like it.
    The feature does some stuff with AI and makes things faster. You should
    definitely try it out when it's ready. We worked hard on this.
    """
    
    log = ExecutionLog("content_example.db")
    
    # Execute pipeline
    print("\n📝 Running content pipeline...")
    result = execute(
        content_pipeline,
        draft=draft.strip(),
        target_tone="professional",
        auto_improve=True,
        log=log,
    )
    
    if result.success:
        print("\n✅ Pipeline completed!")
        print(f"   Execution ID: {result.execution_id}")
        print(f"   Improved: {result.output['was_improved']}")
        print(f"   Stages: {result.output['pipeline_stages']}")
        
        print(f"\n📊 Analysis:")
        analysis = result.output['analysis']
        print(f"   Tone: {analysis.get('tone')}")
        print(f"   Clarity: {analysis.get('clarity_score')}/10")
        print(f"   Engagement: {analysis.get('engagement_score')}/10")
        
        print(f"\n💡 Suggestions ({len(result.output['suggestions'])}):")
        for i, suggestion in enumerate(result.output['suggestions'][:3], 1):
            print(f"   {i}. {suggestion[:80]}...")
        
        print(f"\n🔎 SEO Metadata:")
        seo = result.output['seo']
        print(f"   Title: {seo.get('title')}")
        print(f"   Description: {seo.get('description', '')[:60]}...")
        print(f"   Keywords: {', '.join(seo.get('keywords', [])[:5])}")
        
        if result.output['was_improved']:
            print(f"\n✨ Final Draft:")
            print(f"   {result.output['final_draft'][:150]}...")
        
        # Replay demonstration
        print(f"\n🔁 Replaying pipeline...")
        replay_result = replay(
            content_pipeline,
            execution_id=result.execution_id,
            log=log,
        )
        
        if replay_result.success:
            print(f"   ✅ Replay successful (no divergences)")
            print(f"   Output matches: {replay_result.output == result.output}")
    else:
        print(f"\n❌ Pipeline failed: {result.error}")
    
    print("\n" + "=" * 70)
    print("💾 Pipeline execution saved to: content_example.db")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
