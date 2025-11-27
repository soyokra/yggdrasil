// 侧边栏展开/折叠功能
let isRestoringScroll = false; // 标记是否正在恢复滚动位置

document.addEventListener('DOMContentLoaded', function() {
    // 检查是否有保存的滚动位置
    const savedScrollTop = sessionStorage.getItem('sidebarScrollTop');
    const hasSavedPosition = savedScrollTop !== null;
    
    // 如果有保存的位置，先保存当前滚动位置（防止展开节点时改变）
    if (hasSavedPosition) {
        isRestoringScroll = true;
    }
    
    // 初始化导航树
    initNavTree();
    
    // 设置当前页面的活动状态（会展开相关节点）
    setActiveNavItem();
    
    // 立即初始化滚动监听（必须在恢复前设置，否则会被恢复覆盖）
    initSidebarScrollListener();
    
    // 延迟执行，确保DOM完全渲染和展开完成
    setTimeout(function() {
        // 如果有保存的位置，先恢复滚动位置
        const hasRestored = restoreSidebarScroll();
        
        // 如果恢复了滚动位置，完全保持用户的滚动位置，不再调整
        setTimeout(function() {
            if (hasRestored) {
                // 已经恢复了用户保存的位置，再次确认恢复（防止DOM变化导致位置改变）
                restoreSidebarScroll();
            } else {
                // 没有保存的位置，才确保活动项可见
                ensureActiveItemVisible(false);
            }
            // 如果已经恢复了用户保存的位置，就不做任何调整，完全保持原位置
            
            // 标记恢复完成
            isRestoringScroll = false;
            
            // 保存最终滚动位置（如果用户已经保存过位置，这里保存的就是恢复后的位置）
            saveSidebarScroll();
        }, 200); // 增加延迟，确保DOM变化完成
    }, 50);
});

// 初始化侧边栏滚动监听
function initSidebarScrollListener() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    let scrollTimeout;
    
    // 监听滚动事件，实时保存滚动位置
    sidebar.addEventListener('scroll', function() {
        // 如果正在恢复滚动位置，不保存
        if (isRestoringScroll) return;
        
        // 使用防抖，避免频繁保存
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            saveSidebarScroll();
        }, 150);
    }, { passive: true });
}

// 保存侧边栏滚动位置
function saveSidebarScroll() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar && !isRestoringScroll) {
        const scrollTop = sidebar.scrollTop;
        sessionStorage.setItem('sidebarScrollTop', scrollTop.toString());
    }
}

// 恢复侧边栏滚动位置
function restoreSidebarScroll() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        const savedScrollTop = sessionStorage.getItem('sidebarScrollTop');
        if (savedScrollTop !== null) {
            const scrollTop = parseInt(savedScrollTop, 10);
            // 直接设置滚动位置
            sidebar.scrollTop = scrollTop;
            
            // 使用 requestAnimationFrame 确保在下一帧再次设置，防止DOM变化影响
            requestAnimationFrame(function() {
                sidebar.scrollTop = scrollTop;
            });
            
            return true; // 返回true表示已恢复
        }
    }
    return false; // 返回false表示没有保存的位置
}

// 确保活动项在侧边栏中可见
function ensureActiveItemVisible(hasRestoredPosition) {
    const activeLink = document.querySelector('.nav-link.active');
    if (!activeLink) return;
    
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    
    // 获取活动项和侧边栏的位置信息
    const sidebarRect = sidebar.getBoundingClientRect();
    const activeLinkRect = activeLink.getBoundingClientRect();
    
    // 计算活动项相对于侧边栏的位置
    const linkTop = activeLinkRect.top - sidebarRect.top + sidebar.scrollTop;
    const linkBottom = linkTop + activeLinkRect.height;
    
    // 获取当前可见区域
    const scrollTop = sidebar.scrollTop;
    const scrollBottom = scrollTop + sidebar.clientHeight;
    
    // 如果已恢复用户位置，使用更严格的可见性检查（完全不可见才调整）
    // 如果没有恢复位置，使用宽松的检查（部分可见即可）
    let isVisible;
    let needsScroll = false;
    
    if (hasRestoredPosition) {
        // 严格检查：活动项必须完全在可视区域内
        // 如果活动项完全在可视区域外（上或下），才需要滚动
        const isCompletelyAbove = linkBottom < scrollTop;
        const isCompletelyBelow = linkTop > scrollBottom;
        
        needsScroll = isCompletelyAbove || isCompletelyBelow;
        
        // 如果活动项部分可见，就不需要滚动
        isVisible = !needsScroll;
    } else {
        // 宽松检查：活动项只要部分可见即可
        isVisible = (
            linkBottom > scrollTop &&
            linkTop < scrollBottom
        );
        needsScroll = !isVisible;
    }
    
    // 如果活动项不可见，滚动到它
    if (needsScroll) {
        // 计算最小滚动距离，尽量保持用户的滚动位置
        let targetScrollTop;
        
        if (hasRestoredPosition) {
            // 如果活动项在上方，滚动到刚好能看到它
            // 如果活动项在下方，也是滚动到刚好能看到它
            if (linkBottom < scrollTop) {
                // 活动项在上方，滚动到刚好显示它的位置
                targetScrollTop = linkTop - 20; // 留一点边距
            } else {
                // 活动项在下方，滚动到刚好显示它的位置
                targetScrollTop = linkBottom - sidebar.clientHeight + 20; // 留一点边距
            }
        } else {
            // 没有保存的位置，将活动项放在中央
            targetScrollTop = linkTop - sidebar.clientHeight / 2 + activeLinkRect.height / 2;
        }
        
        // 标记正在恢复，避免触发滚动监听保存
        isRestoringScroll = true;
        sidebar.scrollTop = targetScrollTop;
        
        // 恢复标记
        setTimeout(function() {
            isRestoringScroll = false;
            saveSidebarScroll();
        }, 100);
    }
}

function initNavTree() {
    // 处理箭头点击（展开/折叠）
    const toggleIcons = document.querySelectorAll('.nav-link-icon[data-toggle="collapse"]');
    
    toggleIcons.forEach(icon => {
        icon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const navLink = this.closest('.nav-link');
            const children = navLink ? navLink.nextElementSibling : null;
            
            if (children && children.classList.contains('nav-children')) {
                const isExpanded = children.classList.contains('expanded');
                
                if (isExpanded) {
                    children.classList.remove('expanded');
                    this.classList.remove('expanded');
                } else {
                    children.classList.add('expanded');
                    this.classList.add('expanded');
                }
            }
        });
    });
    
    // 防止目录名称链接点击时触发展开/折叠
    const navLinkTexts = document.querySelectorAll('.nav-link.has-children .nav-link-text');
    navLinkTexts.forEach(textLink => {
        textLink.addEventListener('click', function(e) {
            // 允许链接正常跳转，不阻止默认行为
            e.stopPropagation();
            // 保存滚动位置
            saveSidebarScroll();
        });
    });
    
    // 为所有导航链接添加点击事件，保存滚动位置
    // 使用捕获阶段，确保在跳转前保存
    document.addEventListener('click', function(e) {
        const link = e.target.closest('.nav-link-text[href]');
        if (link) {
            // 立即保存当前滚动位置（用户可能刚滚动过）
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                // 同步保存，确保在页面跳转前完成
                sessionStorage.setItem('sidebarScrollTop', sidebar.scrollTop.toString());
            }
        }
    }, true); // 使用捕获阶段
    
    // 监听页面卸载事件，确保保存最新滚动位置
    window.addEventListener('beforeunload', function() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sessionStorage.setItem('sidebarScrollTop', sidebar.scrollTop.toString());
        }
    });
    
    // 监听页面可见性变化，当用户切换标签页时也保存
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            saveSidebarScroll();
        }
    });
    
    // 默认展开包含当前页面的节点
    const navLinks = document.querySelectorAll('.nav-link.has-children');
    navLinks.forEach(link => {
        const children = link.nextElementSibling;
        if (children && children.classList.contains('nav-children')) {
            if (children.querySelector('.nav-link.active') || children.querySelector('.nav-link-text.active')) {
                children.classList.add('expanded');
                const icon = link.querySelector('.nav-link-icon[data-toggle="collapse"]');
                if (icon) icon.classList.add('expanded');
            }
        }
    });
}

function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinkTexts = document.querySelectorAll('.nav-link-text[data-path]');
    
    navLinkTexts.forEach(linkText => {
        const linkPath = linkText.getAttribute('data-path');
        if (linkPath && (currentPath.endsWith(linkPath) || currentPath.endsWith(linkPath.replace(/\/$/, '/index.html')))) {
            // 添加 active 类到父容器
            const navLink = linkText.closest('.nav-link');
            if (navLink) {
                navLink.classList.add('active');
                linkText.classList.add('active');
            }
            
            // 展开父节点
            let parent = navLink ? navLink.parentElement : null;
            while (parent) {
                if (parent.classList.contains('nav-children')) {
                    parent.classList.add('expanded');
                    const prevSibling = parent.previousElementSibling;
                    if (prevSibling && prevSibling.classList.contains('nav-link')) {
                        prevSibling.classList.add('active');
                        const icon = prevSibling.querySelector('.nav-link-icon[data-toggle="collapse"]');
                        if (icon) icon.classList.add('expanded');
                    }
                }
                parent = parent.parentElement;
            }
        }
    });
}

// 递归展开包含活动项的路径
function expandActivePath() {
    const activeLink = document.querySelector('.nav-link.active');
    if (!activeLink) return;
    
    let current = activeLink.parentElement;
    while (current) {
        if (current.classList.contains('nav-children')) {
            current.classList.add('expanded');
            const prevSibling = current.previousElementSibling;
            if (prevSibling && prevSibling.classList.contains('nav-link')) {
                const icon = prevSibling.querySelector('.nav-link-icon[data-toggle="collapse"]');
                if (icon) icon.classList.add('expanded');
            }
        }
        current = current.parentElement;
    }
}

