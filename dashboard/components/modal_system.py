#!/usr/bin/env python3
"""
Enhanced Modal System for Dashboard Interactions
Provides polished modal dialogs with proper USWDS styling and accessibility.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

import panel as pn
import param
from dashboard.dashboard_logging import get_logger

logger = get_logger(__name__)


class ModalManager(param.Parameterized):
    """
    Centralized modal management system with USWDS styling.
    """

    active_modal = param.Parameter(default=None)
    modal_stack = param.List(default=[])

    def __init__(self, **params: Any) -> None:
        """Initialize the modal manager."""
        super().__init__(**params)
        self.modals = {}
        self.overlay = None
        self._setup_modal_styles()

    def _setup_modal_styles(self) -> None:
        """Setup CSS styles for modals."""
        self.modal_css = """
        <style>
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-in-out;
        }
        
        .modal-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            max-width: 90vw;
            max-height: 90vh;
            overflow: auto;
            animation: slideIn 0.3s ease-in-out;
            position: relative;
        }
        
        .modal-header {
            background-color: #005ea2;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px 8px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-family: 'Merriweather', serif;
            font-size: 1.25rem;
            font-weight: bold;
            margin: 0;
        }
        
        .modal-close {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0.25rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .modal-close:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        .modal-body {
            padding: 1.5rem;
            max-height: 60vh;
            overflow-y: auto;
        }
        
        .modal-footer {
            padding: 1rem 1.5rem;
            border-top: 1px solid #e6e6e6;
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
            background-color: #f0f0f0;
            border-radius: 0 0 8px 8px;
        }
        
        .modal-size-small { width: 400px; }
        .modal-size-medium { width: 600px; }
        .modal-size-large { width: 800px; }
        .modal-size-xlarge { width: 1000px; }
        .modal-size-full { width: 95vw; height: 95vh; }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { 
                opacity: 0;
                transform: translateY(-50px) scale(0.95);
            }
            to { 
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        .modal-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .modal-loading-spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #005ea2;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin-right: 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Accessibility improvements */
        .modal-container:focus {
            outline: 3px solid #ffbe2e;
            outline-offset: 2px;
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .modal-container {
                width: 95vw !important;
                height: 95vh !important;
                margin: 0;
            }
            
            .modal-body {
                max-height: calc(95vh - 140px);
            }
        }
        </style>
        """

    def create_modal(
        self,
        modal_id: str,
        title: str,
        content: Any,
        size: str = "medium",
        actions: Optional[List[Dict[str, Any]]] = None,
        closable: bool = True,
        on_close: Optional[Callable] = None,
    ) -> pn.pane.HTML:
        """
        Create a modal dialog with USWDS styling.

        Args:
            modal_id: Unique identifier for the modal
            title: Modal title
            content: Modal content (can be HTML string or Panel component)
            size: Modal size (small, medium, large, xlarge, full)
            actions: List of action buttons
            closable: Whether modal can be closed
            on_close: Callback function when modal is closed
        """

        # Close button
        close_button = ""
        if closable:
            close_button = f"""
            <button class="modal-close" onclick="closeModal('{modal_id}')" 
                    aria-label="Close modal" title="Close">
                ×
            </button>
            """

        # Action buttons
        actions_html = ""
        if actions:
            action_buttons = []
            for action in actions:
                button_class = action.get("class", "usa-button")
                button_text = action.get("text", "Action")
                button_onclick = action.get("onclick", "")
                button_disabled = "disabled" if action.get("disabled", False) else ""
                action_buttons.append(
                    f'<button class="{button_class}" onclick="{button_onclick}" {button_disabled}>{button_text}</button>'
                )
            actions_html = f'<div class="modal-footer">{"".join(action_buttons)}</div>'

        # Content handling
        content_html = content if isinstance(content, str) else str(content)

        modal_html = f"""
        {self.modal_css}
        
        <div id="modal-{modal_id}" class="modal-overlay" style="display: none;">
            <div class="modal-container modal-size-{size}" role="dialog" 
                 aria-labelledby="modal-title-{modal_id}" aria-modal="true" tabindex="-1">
                <div class="modal-header">
                    <h2 id="modal-title-{modal_id}" class="modal-title">{title}</h2>
                    {close_button}
                </div>
                <div class="modal-body">
                    {content_html}
                </div>
                {actions_html}
            </div>
        </div>
        
        <script>
        function showModal(modalId) {{
            const modal = document.getElementById('modal-' + modalId);
            if (modal) {{
                modal.style.display = 'flex';
                const container = modal.querySelector('.modal-container');
                if (container) {{
                    container.focus();
                }}
                document.body.style.overflow = 'hidden';
                
                // Trap focus within modal
                trapFocus(container);
            }}
        }}
        
        function closeModal(modalId) {{
            const modal = document.getElementById('modal-' + modalId);
            if (modal) {{
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
                
                // Call close callback if provided
                if (window.modalCallbacks && window.modalCallbacks[modalId]) {{
                    window.modalCallbacks[modalId]();
                }}
            }}
        }}
        
        function trapFocus(element) {{
            const focusableElements = element.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            element.addEventListener('keydown', function(e) {{
                if (e.key === 'Tab') {{
                    if (e.shiftKey) {{
                        if (document.activeElement === firstElement) {{
                            lastElement.focus();
                            e.preventDefault();
                        }}
                    }} else {{
                        if (document.activeElement === lastElement) {{
                            firstElement.focus();
                            e.preventDefault();
                        }}
                    }}
                }}
                
                if (e.key === 'Escape') {{
                    closeModal('{modal_id}');
                }}
            }});
        }}
        
        // Close modal when clicking overlay
        document.addEventListener('click', function(e) {{
            if (e.target.classList.contains('modal-overlay')) {{
                const modalId = e.target.id.replace('modal-', '');
                closeModal(modalId);
            }}
        }});
        
        // Initialize modal callbacks
        if (!window.modalCallbacks) {{
            window.modalCallbacks = {{}};
        }}
        
        {f"window.modalCallbacks['{modal_id}'] = {on_close.__name__};" if on_close else ""}
        </script>
        """

        modal_pane = pn.pane.HTML(modal_html, sizing_mode="stretch_width")
        self.modals[modal_id] = modal_pane

        return modal_pane

    def show_modal(self, modal_id: str) -> None:
        """Show a modal by ID."""
        if modal_id in self.modals:
            # Inject JavaScript to show modal
            js_code = f"showModal('{modal_id}');"
            pn.state.add_periodic_callback(
                lambda: None, period=100, count=1
            )  # Trigger update

    def close_modal(self, modal_id: str) -> None:
        """Close a modal by ID."""
        if modal_id in self.modals:
            # Inject JavaScript to close modal
            js_code = f"closeModal('{modal_id}');"
            pn.state.add_periodic_callback(
                lambda: None, period=100, count=1
            )  # Trigger update

    def create_confirmation_modal(
        self,
        title: str,
        message: str,
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        danger: bool = False,
    ) -> str:
        """
        Create a confirmation modal dialog.

        Returns:
            str: Modal ID for showing/closing
        """
        modal_id = f"confirm_{len(self.modals)}"

        confirm_class = "usa-button usa-button--secondary"
        if danger:
            confirm_class = "usa-button usa-button--secondary usa-button--warning"

        actions = [
            {
                "text": cancel_text,
                "class": "usa-button usa-button--outline",
                "onclick": f"closeModal('{modal_id}'); {on_cancel.__name__ if on_cancel else ''}();",
            },
            {
                "text": confirm_text,
                "class": confirm_class,
                "onclick": f"closeModal('{modal_id}'); {on_confirm.__name__}();",
            },
        ]

        content = f"""
        <div class="usa-alert usa-alert--{'warning' if danger else 'info'} usa-alert--no-icon">
            <div class="usa-alert__body">
                <p class="usa-alert__text">{message}</p>
            </div>
        </div>
        """

        self.create_modal(
            modal_id=modal_id,
            title=title,
            content=content,
            size="small",
            actions=actions,
            closable=True,
        )

        return modal_id

    def create_loading_modal(
        self, title: str = "Loading...", message: str = "Please wait"
    ) -> str:
        """
        Create a loading modal dialog.

        Returns:
            str: Modal ID for closing when done
        """
        modal_id = f"loading_{len(self.modals)}"

        content = f"""
        <div class="modal-loading">
            <div class="modal-loading-spinner"></div>
            <div>
                <h3 style="margin: 0 0 0.5rem 0;">{title}</h3>
                <p style="margin: 0; color: #71767a;">{message}</p>
            </div>
        </div>
        """

        self.create_modal(
            modal_id=modal_id,
            title="Processing",
            content=content,
            size="small",
            closable=False,
        )

        return modal_id

    def create_info_modal(self, title: str, content: Any, size: str = "medium") -> str:
        """
        Create an informational modal dialog.

        Returns:
            str: Modal ID for showing/closing
        """
        modal_id = f"info_{len(self.modals)}"

        actions = [
            {
                "text": "Close",
                "class": "usa-button",
                "onclick": f"closeModal('{modal_id}');",
            }
        ]

        self.create_modal(
            modal_id=modal_id,
            title=title,
            content=content,
            size=size,
            actions=actions,
            closable=True,
        )

        return modal_id


# Global modal manager instance
modal_manager = ModalManager()


def show_file_details_modal(file_data: Dict[str, Any]) -> None:
    """Show detailed file information in a modal."""
    content = f"""
    <div class="file-details">
        <div class="usa-summary-box">
            <div class="usa-summary-box__body">
                <h3 class="usa-summary-box__heading">File Information</h3>
                <div class="usa-summary-box__text">
                    <dl class="file-details-list">
                        <dt>Path:</dt>
                        <dd><code>{file_data.get('path', 'N/A')}</code></dd>
                        
                        <dt>Domain:</dt>
                        <dd><span class="usa-tag">{file_data.get('domain', 'Unknown')}</span></dd>
                        
                        <dt>Lines of Code:</dt>
                        <dd>{file_data.get('lines_of_code', 0):,}</dd>
                        
                        <dt>Complexity:</dt>
                        <dd>{file_data.get('complexity', 'N/A')}</dd>
                        
                        <dt>Classes:</dt>
                        <dd>{file_data.get('classes_count', 0)}</dd>
                        
                        <dt>Functions:</dt>
                        <dd>{file_data.get('functions_count', 0)}</dd>
                        
                        <dt>Last Modified:</dt>
                        <dd>{file_data.get('last_modified', 'N/A')}</dd>
                    </dl>
                </div>
            </div>
        </div>
    </div>
    
    <style>
    .file-details-list {
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 0.5rem 1rem;
        margin: 0;
    }
    
    .file-details-list dt {
        font-weight: bold;
        color: #1b1b1b;
    }
    
    .file-details-list dd {
        margin: 0;
        color: #454545;
    }
    
    .file-details-list code {
        background-color: #f0f0f0;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-family: 'Roboto Mono', monospace;
        font-size: 0.9rem;
    }
    </style>
    """

    modal_id = modal_manager.create_info_modal(
        title=f"📄 {file_data.get('name', 'File Details')}",
        content=content,
        size="medium",
    )

    modal_manager.show_modal(modal_id)


def show_analysis_progress_modal() -> str:
    """Show analysis progress modal."""
    return modal_manager.create_loading_modal(
        title="Analyzing Codebase",
        message="Processing files and extracting relationships...",
    )
