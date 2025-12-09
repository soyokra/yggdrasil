# SpringBoot启动流程

![spring_boot](spring_boot.png)

## SpringBoot

| 步骤 | 方法                        | 主要职责 |
|----|---------------------------|---------|
| 1  | createBootstrapContext    | 创建引导上下文，用于早期初始化 |
| 2  | configureHeadlessProperty | 配置系统无头模式属性 |
| 3  | getRunListeners           | 获取SpringApplicationRunListener实例 |
| 4  | listeners.starting()      | 发布ApplicationStartingEvent事件 |
| 5  | prepareEnvironment        | 准备并配置Environment环境对象 |
| 6  | configureIgnoreBeanInfo   | 配置是否忽略BeanInfo类 |
| 7  | printBanner               | 打印Spring Boot启动横幅 |
| 8  | createApplicationContext  | 根据类型创建ApplicationContext |
| 9  | prepareContext            | 准备上下文，加载配置和Bean定义 |
| 10 | refreshContext            | 刷新上下文，初始化所有Bean |
| 11 | afterRefresh              | 刷新后的扩展点，默认空实现 |
| 12 | finishRefresh             | 完成刷新，发布ContextRefreshedEvent |
| 13 | listeners.started()       | 发布ApplicationStartedEvent事件 |
| 14 | callRunners               | 执行ApplicationRunner和CommandLineRunner |
| 15 | listeners.ready()         | 发布ApplicationReadyEvent事件 |
| 16 | handleRunFailure          | 处理启动失败，发布FailedEvent |

## SpringFramework
refresh()是ApplicationContext初始化的核心方法，包含13个步骤：

| 步骤 | 方法 | 主要职责 |
|------|------|----------|
| 1 | prepareRefresh | 准备刷新，初始化环境 |
| 2 | obtainFreshBeanFactory | 获取BeanFactory |
| 3 | prepareBeanFactory | 配置BeanFactory的标准特性 |
| 4 | postProcessBeanFactory | 子类扩展点（Web应用添加作用域） |
| 5 | invokeBeanFactoryPostProcessors | **处理配置类，注册BeanDefinition** |
| 6 | registerBeanPostProcessors | **注册Bean后置处理器** |
| 7 | initMessageSource | 初始化国际化消息源 |
| 8 | initApplicationEventMulticaster | 初始化事件多播器 |
| 9 | onRefresh | 子类扩展点（**创建WebServer**） |
| 10 | registerListeners | 注册监听器 |
| 11 | finishBeanFactoryInitialization | **实例化所有单例Bean** |
| 12 | finishRefresh | 完成刷新（**启动WebServer**） |
| 13 | resetCommonCaches | 清理缓存 |